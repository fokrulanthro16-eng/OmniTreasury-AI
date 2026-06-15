"""Append-only audit trail — every engine decision and human action is recorded here.

In production this writes to UiPath Data Service. In mock mode, records
are kept in-memory and can be exported to a JSON file.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.core.logging_config import get_logger
from src.models.audit import AuditEvent, AuditRecord
from src.models.compliance import ComplianceResult
from src.models.decision import DecisionResult
from src.models.forex import FXResult
from src.models.liquidity import LiquidityResult
from src.models.payment import PaymentRecord
from src.models.risk import RiskResult

logger = get_logger("audit_trail")


class AuditTrail:
    """Append-only in-memory audit ledger with JSON export."""

    def __init__(self) -> None:
        self._records: list[AuditRecord] = []

    # ── Append methods ────────────────────────────────────────────────────────

    def record_payment_received(self, payment: PaymentRecord) -> None:
        self._append(AuditRecord(
            payment_id=payment.payment_id,
            event_type=AuditEvent.PAYMENT_RECEIVED,
            reasoning_summary={
                "amount": str(payment.amount),
                "source_currency": payment.source_currency,
                "target_currency": payment.target_currency,
                "counterparty": payment.counterparty.name,
                "purpose": payment.purpose.value,
            },
            metadata={"submitted_by": payment.submitted_by or "SYSTEM"},
        ))

    def record_compliance(self, compliance: ComplianceResult) -> None:
        self._append(AuditRecord(
            payment_id=compliance.payment_id,
            event_type=AuditEvent.AGENT_ANALYSIS_COMPLETE,
            agent_name="ComplianceAuditorAgent",
            decision=compliance.decision.value,
            confidence_score=compliance.confidence,
            reasoning_summary={
                "sanctions_hits": len(compliance.sanctions_matches),
                "jurisdiction_risks": [j.country for j in compliance.jurisdiction_risks],
                "aml_flags": [f.flag_type for f in compliance.aml_flags],
                "summary": compliance.summary,
            },
            policy_references=compliance.policy_references,
        ))

    def record_forex(self, fx: FXResult) -> None:
        self._append(AuditRecord(
            payment_id=fx.payment_id,
            event_type=AuditEvent.AGENT_ANALYSIS_COMPLETE,
            agent_name="ForexStrategistAgent",
            reasoning_summary={
                "recommended_provider": fx.recommended_provider,
                "recommended_rate": str(fx.recommended_rate),
                "estimated_savings_usd": str(fx.estimated_savings_usd),
                "timing": fx.timing_recommendation.value,
            },
            confidence_score=fx.confidence,
        ))

    def record_liquidity(self, liquidity: LiquidityResult) -> None:
        self._append(AuditRecord(
            payment_id=liquidity.payment_id,
            event_type=AuditEvent.AGENT_ANALYSIS_COMPLETE,
            agent_name="LiquidityBalancerAgent",
            decision=liquidity.status.value,
            reasoning_summary={
                "post_payment_balance": str(liquidity.post_payment_balance),
                "covenant_at_risk": liquidity.covenant_at_risk,
                "netting_available": liquidity.netting_opportunity is not None,
                "recommended_action": liquidity.recommended_action,
            },
            confidence_score=liquidity.confidence,
        ))

    def record_risk(self, risk: RiskResult) -> None:
        self._append(AuditRecord(
            payment_id=risk.payment_id,
            event_type=AuditEvent.AGENT_ANALYSIS_COMPLETE,
            agent_name="RiskIntelligenceAgent",
            reasoning_summary={
                "composite_score": risk.composite_score,
                "risk_level": risk.risk_level.value,
                "limit_breaches": risk.limit_breaches,
                "mitigations": risk.mitigation_recommendations,
            },
            confidence_score=risk.confidence,
        ))

    def record_decision(self, decision: DecisionResult) -> None:
        from src.models.decision import DecisionType
        event_map = {
            DecisionType.AUTO_EXECUTE: AuditEvent.AUTO_DECISION,
            DecisionType.ESCALATE: AuditEvent.CASE_CREATED,
            DecisionType.HARD_REJECT: AuditEvent.PAYMENT_BLOCKED,
        }
        self._append(AuditRecord(
            payment_id=decision.payment_id,
            event_type=event_map[decision.decision],
            agent_name="DecisionOrchestratorAgent",
            decision=decision.decision.value,
            reasoning_summary={
                "rationales": [r.trigger for r in decision.rationales],
                "summary": decision.summary,
                "execution_route": decision.execution_route,
                "escalation_level": decision.escalation_level.value if decision.escalation_level else None,
            },
            confidence_score=decision.confidence,
        ))

    def record_case_created(self, payment_id: str, case_id: str, assigned_role: str) -> None:
        self._append(AuditRecord(
            payment_id=payment_id,
            event_type=AuditEvent.CASE_CREATED,
            agent_name="MaestroClient",
            case_id=case_id,
            reasoning_summary={"assigned_role": assigned_role},
        ))

    def record_human_decision(
        self,
        payment_id: str,
        case_id: str,
        decision: str,
        approver: str,
        notes: str = "",
    ) -> None:
        self._append(AuditRecord(
            payment_id=payment_id,
            event_type=AuditEvent.HUMAN_DECISION,
            decision=decision,
            human_approver=approver,
            human_notes=notes,
            case_id=case_id,
        ))

    def record_execution(self, payment_id: str, confirmation_ref: str) -> None:
        self._append(AuditRecord(
            payment_id=payment_id,
            event_type=AuditEvent.PAYMENT_EXECUTED,
            metadata={"confirmation_ref": confirmation_ref},
        ))

    def record_file_upload(
        self,
        upload_id: str,
        filename: str,
        file_type: str,
        size_bytes: int,
        uploaded_by: str,
        status: str,
        metadata: Optional[dict] = None,
    ) -> None:
        self._append(AuditRecord(
            payment_id=f"UPLOAD-{upload_id}",
            event_type=AuditEvent.FILE_UPLOADED,
            agent_name="DataUploadCenter",
            reasoning_summary={
                "filename": filename,
                "file_type": file_type,
                "size_bytes": size_bytes,
                "status": status,
            },
            metadata={"uploaded_by": uploaded_by, **(metadata or {})},
        ))

    # ── Query methods ─────────────────────────────────────────────────────────

    def get_records_for_payment(self, payment_id: str) -> list[AuditRecord]:
        return [r for r in self._records if r.payment_id == payment_id]

    def get_all_records(self) -> list[AuditRecord]:
        return list(self._records)

    def export_json(self, path: Path) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(
                [r.model_dump(mode="json") for r in self._records],
                fh,
                indent=2,
                default=str,
            )
        logger.info("Audit trail exported", path=str(path), records=len(self._records))

    # ── Internal ──────────────────────────────────────────────────────────────

    def _append(self, record: AuditRecord) -> None:
        self._records.append(record)
        logger.debug(
            "Audit record appended",
            payment_id=record.payment_id,
            event_type=record.event_type.value,
            agent=record.agent_name,
        )


# Module-level singleton used across the pipeline
audit_trail = AuditTrail()
