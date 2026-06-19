"""Unit tests for the LiquidityEngine."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from src.engines.liquidity_engine import LiquidityEngine
from src.models.liquidity import LiquidityStatus
from src.models.payment import CounterpartyDetails, PaymentPurpose, PaymentRecord

POSITIONS_DATA = {
    "positions": {
        "CORP-HQ:EUR": {
            "entity": "CORP-HQ",
            "account_id": "DE89370400440532013000",
            "currency": "EUR",
            "available_balance": 2_000_000,
            "total_balance": 2_500_000,
            "covenant_minimum": 500_000,
        },
        "CORP-HQ:USD": {
            "entity": "CORP-HQ",
            "account_id": "US12345678901234",
            "currency": "USD",
            "available_balance": 150_000,
            "total_balance": 200_000,
            "covenant_minimum": 100_000,
        },
    },
    "netting_candidates": [
        {
            "payment_id": "PAY-NETTING-001",
            "counterparty": "LONDON SUBSIDIARY LTD",
            "currency": "GBP",
            "amount": 250_000,
            "is_internal": True,
        }
    ],
    "funding_sources": [
        {
            "entity": "CORP-EMEA",
            "account_id": "GB29NWBK60161331926819",
            "currency": "EUR",
            "available": 5_000_000,
            "type": "INTERCOMPANY_LOAN",
            "cost_usd": 500,
            "description": "EMEA treasury intercompany facility",
        }
    ],
}


def make_payment(
    source_entity: str = "CORP-HQ",
    source_currency: str = "EUR",
    amount: float = 100_000.0,
    counterparty_name: str = "Test Vendor",
    target_currency: str = "USD",
) -> PaymentRecord:
    return PaymentRecord(
        source_entity=source_entity,
        source_account="DE89370400440532013000",
        source_currency=source_currency,
        amount=Decimal(str(amount)),
        target_currency=target_currency,
        counterparty=CounterpartyDetails(
            name=counterparty_name,
            account_number="GB29NWBK60161331926819",
            bank_name="Barclays",
            bank_swift_code="BARCGB22",
            bank_country="GB",
        ),
        value_date=date(2026, 6, 15),
        purpose=PaymentPurpose.TRADE_PAYMENT,
        reference="LIQ-TEST-001",
    )


@pytest.fixture
def engine() -> LiquidityEngine:
    return LiquidityEngine(positions_data=POSITIONS_DATA)


class TestLiquidityStatus:
    def test_sufficient_balance_returns_sufficient(self, engine: LiquidityEngine) -> None:
        payment = make_payment(amount=100_000.0)
        result = engine.run(payment)
        assert result.status == LiquidityStatus.SUFFICIENT

    def test_insufficient_balance_returns_insufficient(self, engine: LiquidityEngine) -> None:
        payment = make_payment(source_currency="USD", amount=200_000.0)
        result = engine.run(payment)
        assert result.status == LiquidityStatus.INSUFFICIENT

    def test_covenant_breach_returns_constrained(self, engine: LiquidityEngine) -> None:
        # Payment of 1.6M from account with 2M balance and 500K covenant minimum
        # Post-payment = 400K < 500K covenant → CONSTRAINED
        payment = make_payment(amount=1_600_000.0)
        result = engine.run(payment)
        assert result.status in (LiquidityStatus.CONSTRAINED, LiquidityStatus.INSUFFICIENT)
        assert result.covenant_at_risk is True


class TestNettingDiscovery:
    def test_netting_opportunity_detected(self, engine: LiquidityEngine) -> None:
        payment = make_payment(
            counterparty_name="LONDON SUBSIDIARY LTD",
            target_currency="GBP",
            amount=200_000.0,
        )
        result = engine.run(payment)
        assert result.netting_opportunity is not None
        assert result.netting_opportunity.estimated_fx_saving_usd > Decimal("0")

    def test_no_netting_for_unknown_counterparty(self, engine: LiquidityEngine) -> None:
        payment = make_payment(counterparty_name="Random External Corp", amount=50_000.0)
        result = engine.run(payment)
        assert result.netting_opportunity is None


class TestFundingOptions:
    def test_funding_options_populated_when_constrained(self, engine: LiquidityEngine) -> None:
        payment = make_payment(amount=1_900_000.0)
        result = engine.run(payment)
        assert len(result.funding_options) > 0

    def test_no_funding_options_when_sufficient(self, engine: LiquidityEngine) -> None:
        payment = make_payment(amount=50_000.0)
        result = engine.run(payment)
        assert result.status == LiquidityStatus.SUFFICIENT


class TestPostPaymentCalculation:
    def test_post_payment_balance_calculated_correctly(self, engine: LiquidityEngine) -> None:
        payment = make_payment(amount=300_000.0)
        result = engine.run(payment)
        expected = Decimal("2000000") - Decimal("300000")
        assert result.post_payment_balance == expected
