"""Decision orchestration engine: synthesises all agent outputs into a final decision.

Decision matrix:
  Compliance BLOCK                         → HARD_REJECT
  Compliance FLAG                          → ESCALATE (Compliance Officer / Legal)
  Liquidity INSUFFICIENT                   → ESCALATE (Treasury Manager)
  Risk composite ≥ HIGH_RISK_THRESHOLD     → ESCALATE (Treasury Manager)
  Risk composite ≥ ESCALATION_THRESHOLD    → ESCALATE (Treasury Manager)
  Amount ≥ MATERIALITY_THRESHOLD           → ESCALATE (CFO)
  All clear                                → AUTO_EXECUTE
"""

from __future__ import annotations

from src.core.config import settings
from src.core.logging_config import get_logger
from src.models.compliance import ComplianceDecision, ComplianceResult
from src.models.decision import (
    CasePayload,
    DecisionRationale,
    DecisionResult,
    DecisionType,
    EscalationLevel,
)
from src.models.forex import FXResult
from src.models.liquidity import LiquidityResult, LiquidityStatus
from src.models.payment import PaymentRecord
from src.models.risk import RiskLevel, RiskResult

logger = get_logger("decision_engine")

_SLA_BY_LEVEL: dict[EscalationLevel, int] = {
    EscalationLevel.COMPLIANCE_OFFICER: 240,   # 4 hours
    EscalationLevel.TREASURY_MANAGER: 120,     # 2 hours
    EscalationLevel.CFO: 480,                  # 8 hours
    EscalationLevel.LEGAL: 1440,               # 24 hours
}


class DecisionEngine:
    """Applies the treasury decision matrix and produces an actionable DecisionResult."""

    def run(
        self,
        payment: PaymentRecord,
        compliance: ComplianceResult,
        fx: FXResult,
        liquidity: LiquidityResult,
        risk: RiskResult,
    ) -> DecisionResult:
        logger.info("Running decision synthesis", payment_id=payment.payment_id)

        rationales: list[DecisionRationale] = []
        decision_type: DecisionType
        escalation_level: EscalationLevel | None = None

        # ── Rule 1: Compliance BLOCK ──────────────────────────────────────────
        if compliance.decision == ComplianceDecision.BLOCK:
            decision_type = DecisionType.HARD_REJECT
            rationales.append(
                DecisionRationale(
                    trigger="COMPLIANCE_BLOCK",
                    description=(
                        f"Payment BLOCKED by compliance engine. "
                        f"{compliance.summary}"
                    ),
                    agent_source="ComplianceAuditorAgent",
                )
            )
            return self._build_result(
                payment, decision_type, escalation_level, rationales,
                compliance, fx, liquidity, risk
            )

        # ── Rule 2: Compliance FLAG ───────────────────────────────────────────
        if compliance.decision == ComplianceDecision.FLAG:
            decision_type = DecisionType.ESCALATE
            escalation_level = self._map_compliance_approver(compliance)
            rationales.append(
                DecisionRationale(
                    trigger="COMPLIANCE_FLAG",
                    description=f"Compliance FLAG: {compliance.summary}",
                    agent_source="ComplianceAuditorAgent",
                )
            )

        # ── Rule 3: Liquidity INSUFFICIENT ───────────────────────────────────
        elif liquidity.status == LiquidityStatus.INSUFFICIENT:
            decision_type = DecisionType.ESCALATE
            escalation_level = EscalationLevel.TREASURY_MANAGER
            rationales.append(
                DecisionRationale(
                    trigger="LIQUIDITY_INSUFFICIENT",
                    description=(
                        f"Insufficient funds in {payment.source_entity} "
                        f"({payment.source_currency}). "
                        f"Post-payment balance: {liquidity.post_payment_balance}."
                    ),
                    agent_source="LiquidityBalancerAgent",
                )
            )

        # ── Rule 4: Critical risk ─────────────────────────────────────────────
        elif risk.composite_score >= settings.high_risk_threshold:
            decision_type = DecisionType.ESCALATE
            escalation_level = EscalationLevel.TREASURY_MANAGER
            rationales.append(
                DecisionRationale(
                    trigger="HIGH_RISK_SCORE",
                    description=(
                        f"Composite risk score {risk.composite_score:.1f} ≥ "
                        f"threshold {settings.high_risk_threshold}. "
                        f"Risk level: {risk.risk_level.value}. "
                        f"Breaches: {', '.join(risk.limit_breaches) or 'none'}."
                    ),
                    agent_source="RiskIntelligenceAgent",
                )
            )

        # ── Rule 5: Elevated risk ─────────────────────────────────────────────
        elif risk.composite_score >= settings.risk_escalation_threshold:
            decision_type = DecisionType.ESCALATE
            escalation_level = EscalationLevel.TREASURY_MANAGER
            rationales.append(
                DecisionRationale(
                    trigger="ELEVATED_RISK_SCORE",
                    description=(
                        f"Risk score {risk.composite_score:.1f} exceeds escalation "
                        f"threshold {settings.risk_escalation_threshold}."
                    ),
                    agent_source="RiskIntelligenceAgent",
                )
            )

        # ── Rule 6: Materiality threshold (CFO approval) ─────────────────────
        elif float(payment.amount) >= settings.materiality_threshold:
            decision_type = DecisionType.ESCALATE
            escalation_level = EscalationLevel.CFO
            rationales.append(
                DecisionRationale(
                    trigger="MATERIALITY_THRESHOLD",
                    description=(
                        f"Payment amount {float(payment.amount):,.2f} {payment.source_currency} "
                        f"exceeds materiality threshold ${settings.materiality_threshold:,.0f}. "
                        "CFO approval required."
                    ),
                    agent_source="DecisionOrchestratorAgent",
                )
            )

        # ── Rule 7: Auto-approve ──────────────────────────────────────────────
        else:
            decision_type = DecisionType.AUTO_EXECUTE
            rationales.append(
                DecisionRationale(
                    trigger="ALL_CLEAR",
                    description=(
                        f"All checks passed. Compliance: {compliance.decision.value}. "
                        f"Risk: {risk.composite_score:.1f}/{settings.risk_escalation_threshold}. "
                        f"Liquidity: {liquidity.status.value}."
                    ),
                    agent_source="DecisionOrchestratorAgent",
                )
            )

        result = self._build_result(
            payment, decision_type, escalation_level, rationales,
            compliance, fx, liquidity, risk
        )

        logger.info(
            "Decision complete",
            payment_id=payment.payment_id,
            decision=decision_type.value,
            escalation_level=escalation_level.value if escalation_level else None,
        )
        return result

    # ── Result builder ────────────────────────────────────────────────────────

    def _build_result(
        self,
        payment: PaymentRecord,
        decision_type: DecisionType,
        escalation_level: EscalationLevel | None,
        rationales: list[DecisionRationale],
        compliance: ComplianceResult,
        fx: FXResult,
        liquidity: LiquidityResult,
        risk: RiskResult,
    ) -> DecisionResult:
        case_payload: CasePayload | None = None

        if decision_type == DecisionType.ESCALATE and escalation_level:
            case_payload = self._build_case_payload(
                payment, escalation_level, rationales,
                compliance, fx, liquidity, risk
            )

        execution_route: str | None = None
        if decision_type == DecisionType.AUTO_EXECUTE and fx.best_route:
            execution_route = fx.best_route.provider

        summary = self._build_summary(decision_type, escalation_level, rationales)

        return DecisionResult(
            payment_id=payment.payment_id,
            decision=decision_type,
            escalation_level=escalation_level,
            rationales=rationales,
            execution_route=execution_route,
            case_payload=case_payload,
            summary=summary,
            compliance_result=compliance,
            fx_result=fx,
            liquidity_result=liquidity,
            risk_result=risk,
        )

    def _build_case_payload(
        self,
        payment: PaymentRecord,
        level: EscalationLevel,
        rationales: list[DecisionRationale],
        compliance: ComplianceResult,
        fx: FXResult,
        liquidity: LiquidityResult,
        risk: RiskResult,
    ) -> CasePayload:
        priority = "CRITICAL" if level == EscalationLevel.LEGAL else (
            "HIGH" if level in (EscalationLevel.COMPLIANCE_OFFICER, EscalationLevel.CFO) else "MEDIUM"
        )
        title_prefix = {
            EscalationLevel.COMPLIANCE_OFFICER: "[COMPLIANCE FLAG]",
            EscalationLevel.TREASURY_MANAGER: "[TREASURY REVIEW]",
            EscalationLevel.CFO: "[CFO APPROVAL]",
            EscalationLevel.LEGAL: "[LEGAL HOLD]",
        }.get(level, "[REVIEW]")

        return CasePayload(
            case_title=(
                f"{title_prefix} {payment.source_currency} "
                f"{float(payment.amount):,.0f} → {payment.counterparty.name}"
            ),
            case_type="TreasuryPaymentException",
            priority=priority,
            assigned_role=level,
            sla_minutes=_SLA_BY_LEVEL[level],
            payment_summary={
                "payment_id": payment.payment_id,
                "amount": str(payment.amount),
                "source_currency": payment.source_currency,
                "target_currency": payment.target_currency,
                "counterparty": payment.counterparty.name,
                "counterparty_country": payment.counterparty.bank_country,
                "purpose": payment.purpose.value,
                "value_date": str(payment.value_date),
                "reference": payment.reference,
            },
            compliance_report={
                "decision": compliance.decision.value,
                "sanctions_hits": len(compliance.sanctions_matches),
                "jurisdiction_risks": [j.model_dump() for j in compliance.jurisdiction_risks],
                "aml_flags": len(compliance.aml_flags),
                "policy_references": compliance.policy_references,
                "summary": compliance.summary,
            },
            risk_report={
                "composite_score": risk.composite_score,
                "risk_level": risk.risk_level.value,
                "limit_breaches": risk.limit_breaches,
                "mitigations": risk.mitigation_recommendations,
            },
            fx_analysis={
                "recommended_provider": fx.recommended_provider,
                "recommended_rate": str(fx.recommended_rate),
                "estimated_savings_usd": str(fx.estimated_savings_usd),
                "timing": fx.timing_recommendation.value,
                "volatility_flag": fx.volatility_flag,
            },
            liquidity_status={
                "status": liquidity.status.value,
                "post_payment_balance": str(liquidity.post_payment_balance),
                "covenant_at_risk": liquidity.covenant_at_risk,
                "recommended_action": liquidity.recommended_action,
            },
            agent_recommendations=[r.description for r in rationales],
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _map_compliance_approver(compliance: ComplianceResult) -> EscalationLevel:
        recommended = compliance.recommended_approver or ""
        if recommended == "LEGAL":
            return EscalationLevel.LEGAL
        return EscalationLevel.COMPLIANCE_OFFICER

    @staticmethod
    def _build_summary(
        decision_type: DecisionType,
        escalation_level: EscalationLevel | None,
        rationales: list[DecisionRationale],
    ) -> str:
        if decision_type == DecisionType.AUTO_EXECUTE:
            return "Payment approved for automatic execution. All compliance, risk, and liquidity checks passed."
        if decision_type == DecisionType.HARD_REJECT:
            return f"Payment BLOCKED. {rationales[0].description if rationales else ''}"
        level_str = escalation_level.value if escalation_level else "REVIEWER"
        trigger = rationales[0].trigger if rationales else "POLICY"
        return f"Payment escalated to {level_str} for review. Trigger: {trigger}."
