"""Unit tests for the ForexEngine."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from src.engines.forex_engine import ForexEngine
from src.models.forex import FXTimingRecommendation
from src.models.payment import CounterpartyDetails, PaymentPurpose, PaymentRecord, PaymentUrgency

FX_DATA = {
    "rates": {
        "EUR/USD": 1.0842,
        "GBP/USD": 1.2630,
        "USD/JPY": 148.50,
        "USD/CHF": 0.8820,
        "USD/TRY": 32.15,
    },
    "volatility": {
        "USD/TRY": 0.25,
        "EUR/USD": 0.04,
    },
    "trends": {
        "EUR/USD": "STABLE",
        "GBP/USD": "IMPROVING",
    },
}


def make_payment(
    source_currency: str = "EUR",
    target_currency: str = "USD",
    amount: float = 100_000.0,
    urgency: PaymentUrgency = PaymentUrgency.T_PLUS_2,
) -> PaymentRecord:
    return PaymentRecord(
        source_entity="CORP-HQ",
        source_account="ACC-001",
        source_currency=source_currency,
        amount=Decimal(str(amount)),
        target_currency=target_currency,
        counterparty=CounterpartyDetails(
            name="Test Vendor Inc",
            account_number="US12345678",
            bank_name="JPMorgan Chase",
            bank_swift_code="CHASUS33",
            bank_country="US",
        ),
        value_date=date(2026, 6, 15),
        purpose=PaymentPurpose.TRADE_PAYMENT,
        reference="FX-TEST-001",
        urgency=urgency,
    )


@pytest.fixture
def engine() -> ForexEngine:
    return ForexEngine(fx_data=FX_DATA)


class TestRateFetching:
    def test_benchmark_rate_fetched_for_known_pair(self, engine: ForexEngine) -> None:
        rate = engine._get_benchmark_rate("EUR/USD")
        assert rate == Decimal("1.0842")

    def test_inverse_rate_computed(self, engine: ForexEngine) -> None:
        rate = engine._get_benchmark_rate("USD/EUR")
        assert rate > Decimal("0.9") and rate < Decimal("0.95")

    def test_unknown_pair_returns_one(self, engine: ForexEngine) -> None:
        rate = engine._get_benchmark_rate("XXX/YYY")
        assert rate == Decimal("1")

    def test_three_quotes_returned(self, engine: ForexEngine) -> None:
        quotes = engine._fetch_provider_quotes("EUR/USD", Decimal("1.0842"))
        assert len(quotes) == 3


class TestRouteRanking:
    def test_routes_sorted_best_first(self, engine: ForexEngine) -> None:
        payment = make_payment()
        result = engine.run(payment)
        nets = [r.net_amount_target for r in result.ranked_routes]
        assert nets == sorted(nets, reverse=True)

    def test_recommended_provider_is_best_route(self, engine: ForexEngine) -> None:
        payment = make_payment()
        result = engine.run(payment)
        assert result.recommended_provider == result.ranked_routes[0].provider


class TestTimingRecommendation:
    def test_same_day_urgency_forces_execute_now(self, engine: ForexEngine) -> None:
        payment = make_payment(urgency=PaymentUrgency.SAME_DAY)
        result = engine.run(payment)
        assert result.timing_recommendation == FXTimingRecommendation.EXECUTE_NOW

    def test_high_volatility_recommends_hedge(self, engine: ForexEngine) -> None:
        payment = make_payment(source_currency="USD", target_currency="TRY", amount=500_000.0)
        result = engine.run(payment)
        assert result.volatility_flag is True


class TestSavingsCalculation:
    def test_savings_non_negative(self, engine: ForexEngine) -> None:
        payment = make_payment()
        result = engine.run(payment)
        assert result.estimated_savings_usd >= Decimal("0")

    def test_result_has_all_required_fields(self, engine: ForexEngine) -> None:
        payment = make_payment()
        result = engine.run(payment)
        assert result.payment_id == payment.payment_id
        assert result.currency_pair == "EUR/USD"
        assert result.benchmark_rate > Decimal("0")
        assert len(result.ranked_routes) == 3
