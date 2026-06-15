"""Demo data generator — runs the full pipeline on all sample payments and
assembles a DemoState that every dashboard module can consume.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

import structlog

from src.models.compliance import ComplianceResult
from src.models.decision import DecisionResult
from src.models.forex import FXResult
from src.models.liquidity import LiquidityResult
from src.models.payment import PaymentRecord
from src.models.risk import RiskResult


@dataclass
class PipelineRun:
    payment: PaymentRecord
    decision: DecisionResult
    compliance: Optional[ComplianceResult] = None
    fx: Optional[FXResult] = None
    liquidity: Optional[LiquidityResult] = None
    risk: Optional[RiskResult] = None
    maestro_case_id: Optional[str] = None
    bank_confirmation: Optional[str] = None
    processing_ms: float = 0.0


@dataclass
class DemoState:
    runs: list[PipelineRun] = field(default_factory=list)

    # Synthetic historical context — makes dashboards look like a real workday
    historical_payment_count: int = 47
    historical_auto_executed: int = 38
    historical_escalated: int = 7
    historical_hard_rejected: int = 2
    historical_total_value_m: float = 12.4
    historical_fx_savings_usd: Decimal = Decimal("89420")
    historical_avg_risk_score: float = 24.3
    historical_processing_time_ms: float = 847.0


def build_demo_state(verbose: bool = False) -> DemoState:
    """Run all sample payments through the full pipeline and return a DemoState.

    Logging is suppressed to WARNING during the build so the terminal stays clean
    for the dashboard output that follows.
    """
    # Silence structlog during pipeline run unless verbose
    target_level = logging.INFO if verbose else logging.WARNING
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(target_level),
    )

    from src.agents.decision_orchestrator import DecisionOrchestratorAgent
    from src.integrations.mock_banking_api import MockBankingAPIClient
    from src.integrations.mock_erp import MockERPClient
    from src.integrations.uipath_maestro import MaestroClient
    from src.models.decision import DecisionType
    from src.utils.audit_trail import audit_trail

    erp = MockERPClient()
    payments = erp.get_pending_payments()
    orchestrator = DecisionOrchestratorAgent()
    banking = MockBankingAPIClient()
    maestro = MaestroClient()

    runs: list[PipelineRun] = []

    for payment in payments:
        t0 = time.perf_counter()
        audit_trail.record_payment_received(payment)
        decision = orchestrator.analyse(payment)

        if decision.compliance_result:
            audit_trail.record_compliance(decision.compliance_result)
        if decision.fx_result:
            audit_trail.record_forex(decision.fx_result)
        if decision.liquidity_result:
            audit_trail.record_liquidity(decision.liquidity_result)
        if decision.risk_result:
            audit_trail.record_risk(decision.risk_result)
        audit_trail.record_decision(decision)

        run = PipelineRun(
            payment=payment,
            decision=decision,
            compliance=decision.compliance_result,
            fx=decision.fx_result,
            liquidity=decision.liquidity_result,
            risk=decision.risk_result,
            processing_ms=(time.perf_counter() - t0) * 1000,
        )

        if decision.decision == DecisionType.AUTO_EXECUTE and decision.fx_result:
            conf = banking.submit_payment(
                payment,
                fx_provider=decision.execution_route or "JP Morgan Treasury",
                execution_rate=decision.fx_result.recommended_rate,
            )
            audit_trail.record_execution(payment.payment_id, conf)
            run.bank_confirmation = conf

        elif decision.decision == DecisionType.ESCALATE and decision.case_payload:
            case_id = maestro.create_case(decision.case_payload)
            audit_trail.record_case_created(
                payment.payment_id, case_id, decision.case_payload.assigned_role.value
            )
            run.maestro_case_id = case_id

        runs.append(run)

    # Restore logging to INFO for dashboard display
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    )

    avg_ms = sum(r.processing_ms for r in runs) / max(len(runs), 1)
    total_fx = sum(r.fx.estimated_savings_usd for r in runs if r.fx)

    return DemoState(
        runs=runs,
        historical_fx_savings_usd=Decimal("89420") + total_fx,
        historical_processing_time_ms=avg_ms,
    )


def _infer_scenario_tag(payment: PaymentRecord) -> str:
    """Reverse-map payment characteristics to a scenario tag for display."""
    ref = payment.reference.lower()
    name = payment.counterparty.name.lower()
    country = payment.counterparty.bank_country.upper()

    if country in ("IR", "KP", "MM"):
        return "COMPLIANCE_BLOCK"
    if "iran" in name or "tehran" in name or "pyongyang" in name:
        return "SANCTIONS_FLAG"
    if float(payment.amount) >= 1_000_000:
        return "CFO_APPROVAL"
    if "structur" in ref or "aml" in ref:
        return "AML_STRUCTURING"
    return payment.scenario or "CLEAN_PAYMENT"
