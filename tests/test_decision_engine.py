"""Unit tests for the DecisionEngine."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest

from src.engines.decision_engine import DecisionEngine
from src.models.compliance import ComplianceDecision, ComplianceResult
from src.models.decision import DecisionType, EscalationLevel
from src.models.forex import FXResult, FXRoute, FXTimingRecommendation
from src.models.liquidity import CashPosition, LiquidityResult, LiquidityStatus
from src.models.payment import CounterpartyDetails, PaymentPurpose, PaymentRecord
from src.models.risk import RiskLevel, RiskResult


def make_payment(amount: float = 100_000.0) -> PaymentRecord:
    return PaymentRecord(
        source_entity="CORP-HQ",
        source_account="ACC-001",
        source_currency="EUR",
        amount=Decimal(str(amount)),
        target_currency="USD",
        counterparty=CounterpartyDetails(
            name="Test Vendor Corp",
            account_number="TESTACC",
            bank_name="Test Bank",
            bank_swift_code="TESTUS33",
            bank_country="US",
        ),
        value_date=date(2026, 6, 15),
        purpose=PaymentPurpose.TRADE_PAYMENT,
        reference="DEC-TEST-001",
    )


def make_compliance(decision: ComplianceDecision, confidence: float = 0.95) -> ComplianceResult:
    return ComplianceResult(
        payment_id="TEST",
        decision=decision,
        confidence=confidence,
        summary=f"Decision: {decision.value}.",
    )


def make_fx() -> FXResult:
    route = FXRoute(
        rank=1,
        provider="HSBC Global FX",
        rate=Decimal("1.0850"),
        gross_amount_target=Decimal("108500"),
        transaction_fee_usd=Decimal("25"),
        net_amount_target=Decimal("108475"),
        total_cost_usd=Decimal("25"),
        savings_vs_benchmark_usd=Decimal("320"),
    )
    return FXResult(
        payment_id="TEST",
        currency_pair="EUR/USD",
        payment_amount=Decimal("100000"),
        benchmark_rate=Decimal("1.0820"),
        ranked_routes=[route],
        recommended_provider="HSBC Global FX",
        recommended_rate=Decimal("1.0850"),
        estimated_savings_usd=Decimal("320"),
        savings_bps=29.6,
        timing_recommendation=FXTimingRecommendation.EXECUTE_NOW,
    )


def make_liquidity(status: LiquidityStatus) -> LiquidityResult:
    position = CashPosition(
        entity="CORP-HQ",
        account_id="ACC-001",
        currency="EUR",
        available_balance=Decimal("2000000"),
        total_balance=Decimal("2500000"),
        covenant_minimum=Decimal("500000"),
    )
    return LiquidityResult(
        payment_id="TEST",
        status=status,
        source_position=position,
        post_payment_balance=Decimal("1900000"),
        post_payment_headroom=Decimal("1400000"),
        covenant_at_risk=False,
    )


def make_risk(score: float) -> RiskResult:
    level = (
        RiskLevel.CRITICAL if score >= 80 else
        RiskLevel.HIGH if score >= 60 else
        RiskLevel.MEDIUM if score >= 35 else
        RiskLevel.LOW
    )
    return RiskResult(
        payment_id="TEST",
        composite_score=score,
        risk_level=level,
    )


@pytest.fixture
def engine() -> DecisionEngine:
    return DecisionEngine()


class TestDecisionMatrix:
    def test_all_clear_returns_auto_execute(self, engine: DecisionEngine) -> None:
        payment = make_payment(amount=100_000.0)
        result = engine.run(
            payment,
            make_compliance(ComplianceDecision.CLEAR),
            make_fx(),
            make_liquidity(LiquidityStatus.SUFFICIENT),
            make_risk(25.0),
        )
        assert result.decision == DecisionType.AUTO_EXECUTE

    def test_compliance_block_returns_hard_reject(self, engine: DecisionEngine) -> None:
        payment = make_payment()
        result = engine.run(
            payment,
            make_compliance(ComplianceDecision.BLOCK),
            make_fx(),
            make_liquidity(LiquidityStatus.SUFFICIENT),
            make_risk(10.0),
        )
        assert result.decision == DecisionType.HARD_REJECT

    def test_compliance_flag_returns_escalate_to_compliance_officer(self, engine: DecisionEngine) -> None:
        payment = make_payment()
        result = engine.run(
            payment,
            make_compliance(ComplianceDecision.FLAG),
            make_fx(),
            make_liquidity(LiquidityStatus.SUFFICIENT),
            make_risk(10.0),
        )
        assert result.decision == DecisionType.ESCALATE
        assert result.escalation_level == EscalationLevel.COMPLIANCE_OFFICER

    def test_insufficient_liquidity_escalates_to_treasury_manager(self, engine: DecisionEngine) -> None:
        payment = make_payment()
        result = engine.run(
            payment,
            make_compliance(ComplianceDecision.CLEAR),
            make_fx(),
            make_liquidity(LiquidityStatus.INSUFFICIENT),
            make_risk(10.0),
        )
        assert result.decision == DecisionType.ESCALATE
        assert result.escalation_level == EscalationLevel.TREASURY_MANAGER

    def test_high_risk_score_escalates_to_treasury_manager(self, engine: DecisionEngine) -> None:
        payment = make_payment()
        result = engine.run(
            payment,
            make_compliance(ComplianceDecision.CLEAR),
            make_fx(),
            make_liquidity(LiquidityStatus.SUFFICIENT),
            make_risk(75.0),
        )
        assert result.decision == DecisionType.ESCALATE
        assert result.escalation_level == EscalationLevel.TREASURY_MANAGER

    def test_materiality_threshold_escalates_to_cfo(self, engine: DecisionEngine) -> None:
        payment = make_payment(amount=1_500_000.0)
        result = engine.run(
            payment,
            make_compliance(ComplianceDecision.CLEAR),
            make_fx(),
            make_liquidity(LiquidityStatus.SUFFICIENT),
            make_risk(20.0),
        )
        assert result.decision == DecisionType.ESCALATE
        assert result.escalation_level == EscalationLevel.CFO


class TestCasePayload:
    def test_case_payload_created_on_escalation(self, engine: DecisionEngine) -> None:
        payment = make_payment()
        result = engine.run(
            payment,
            make_compliance(ComplianceDecision.FLAG),
            make_fx(),
            make_liquidity(LiquidityStatus.SUFFICIENT),
            make_risk(10.0),
        )
        assert result.case_payload is not None
        assert result.case_payload.case_title != ""
        assert result.case_payload.sla_minutes > 0

    def test_no_case_payload_on_auto_execute(self, engine: DecisionEngine) -> None:
        payment = make_payment()
        result = engine.run(
            payment,
            make_compliance(ComplianceDecision.CLEAR),
            make_fx(),
            make_liquidity(LiquidityStatus.SUFFICIENT),
            make_risk(15.0),
        )
        assert result.case_payload is None

    def test_execution_route_set_on_auto_execute(self, engine: DecisionEngine) -> None:
        payment = make_payment()
        result = engine.run(
            payment,
            make_compliance(ComplianceDecision.CLEAR),
            make_fx(),
            make_liquidity(LiquidityStatus.SUFFICIENT),
            make_risk(15.0),
        )
        assert result.execution_route is not None
