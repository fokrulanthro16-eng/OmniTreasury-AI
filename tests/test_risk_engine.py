"""Unit tests for the RiskEngine."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from src.engines.risk_engine import RiskEngine
from src.models.payment import CounterpartyDetails, PaymentPurpose, PaymentRecord
from src.models.risk import RiskLevel

THRESHOLDS = {
    "concentration_limits": {
        "single_country_usd": 5_000_000,
        "single_bank_usd": 2_000_000,
    }
}


def make_payment(
    bank_country: str = "DE",
    bank_name: str = "Deutsche Bank",
    amount: float = 100_000.0,
    source_currency: str = "EUR",
    target_currency: str = "USD",
    submitted_by: str | None = "treasury@corp.com",
    invoice_reference: str | None = "INV-2024-001",
) -> PaymentRecord:
    return PaymentRecord(
        source_entity="CORP-HQ",
        source_account="ACC-001",
        source_currency=source_currency,
        amount=Decimal(str(amount)),
        target_currency=target_currency,
        counterparty=CounterpartyDetails(
            name="Test Vendor Corp",
            account_number="TESTACC001",
            bank_name=bank_name,
            bank_swift_code="DEUTDEFF",
            bank_country=bank_country,
        ),
        value_date=date(2026, 6, 15),
        purpose=PaymentPurpose.TRADE_PAYMENT,
        reference="RISK-TEST-001",
        submitted_by=submitted_by,
        invoice_reference=invoice_reference,
    )


@pytest.fixture
def engine() -> RiskEngine:
    return RiskEngine(thresholds_data=THRESHOLDS)


class TestCompositeScore:
    def test_low_risk_payment_scores_below_40(self, engine: RiskEngine) -> None:
        payment = make_payment(bank_country="DE", amount=50_000.0)
        result = engine.run(payment)
        assert result.composite_score < 60

    def test_high_risk_country_increases_score(self, engine: RiskEngine) -> None:
        low = engine.run(make_payment(bank_country="DE", amount=50_000.0))
        high = engine.run(make_payment(bank_country="RU", amount=50_000.0))
        assert high.composite_score > low.composite_score

    def test_volatile_currency_increases_score(self, engine: RiskEngine) -> None:
        stable = engine.run(make_payment(source_currency="EUR", target_currency="USD"))
        volatile = engine.run(make_payment(source_currency="USD", target_currency="TRY"))
        assert volatile.composite_score > stable.composite_score

    def test_score_bounded_0_to_100(self, engine: RiskEngine) -> None:
        payment = make_payment(bank_country="RU", amount=10_000_000.0, target_currency="TRY")
        result = engine.run(payment)
        assert 0.0 <= result.composite_score <= 100.0


class TestRiskLevel:
    def test_low_score_maps_to_low_level(self, engine: RiskEngine) -> None:
        payment = make_payment(bank_country="CH", amount=10_000.0)
        result = engine.run(payment)
        assert result.risk_level in (RiskLevel.LOW, RiskLevel.MEDIUM)

    def test_critical_risk_level_on_extreme_score(self, engine: RiskEngine) -> None:
        payment = make_payment(bank_country="RU", amount=8_000_000.0, target_currency="TRY")
        result = engine.run(payment)
        assert result.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)


class TestConcentrationChecks:
    def test_concentration_check_included_in_result(self, engine: RiskEngine) -> None:
        payment = make_payment()
        result = engine.run(payment)
        assert len(result.concentration_checks) >= 2

    def test_over_limit_payment_shows_breach(self, engine: RiskEngine) -> None:
        payment = make_payment(amount=6_000_000.0)
        result = engine.run(payment)
        breached = [c for c in result.concentration_checks if c.breached]
        assert len(breached) > 0


class TestOperationalFlags:
    def test_materiality_flag_on_large_payment(self, engine: RiskEngine) -> None:
        from src.core.config import settings
        payment = make_payment(amount=float(settings.materiality_threshold) + 1)
        result = engine.run(payment)
        flag_types = [f.flag_type for f in result.operational_flags]
        assert "MATERIALITY" in flag_types

    def test_missing_invoice_increases_operational_score(self, engine: RiskEngine) -> None:
        with_inv = engine.run(make_payment(invoice_reference="INV-001"))
        without_inv = engine.run(make_payment(invoice_reference=None))
        op_with = next(f for f in with_inv.factors if f.category.value == "OPERATIONAL")
        op_without = next(f for f in without_inv.factors if f.category.value == "OPERATIONAL")
        assert op_without.score > op_with.score
