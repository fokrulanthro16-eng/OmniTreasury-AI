"""FX optimisation engine: multi-provider rate comparison, route ranking, savings calculation."""

from __future__ import annotations

import json
import random
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from src.core.config import settings
from src.core.exceptions import FXEngineError
from src.core.logging_config import get_logger
from src.models.forex import (
    FXResult,
    FXRoute,
    FXTimingRecommendation,
    HedgeOpportunity,
    RateQuote,
)
from src.models.payment import PaymentRecord, PaymentUrgency

logger = get_logger("forex_engine")

_CENTS = Decimal("0.0001")


class ForexEngine:
    """Fetches multi-provider quotes, ranks routes by total cost, and recommends execution timing."""

    def __init__(self, fx_data: dict[str, Any] | None = None) -> None:
        self._fx_data = fx_data or self._load_default_rates()
        logger.info("ForexEngine initialised", pairs=len(self._fx_data.get("rates", {})))

    # ── Public interface ──────────────────────────────────────────────────────

    def run(self, payment: PaymentRecord) -> FXResult:
        """Produce a full FX analysis for the given payment."""
        logger.info(
            "Running FX analysis",
            payment_id=payment.payment_id,
            pair=payment.currency_pair,
        )

        pair = payment.currency_pair
        amount = payment.amount

        benchmark_rate = self._get_benchmark_rate(pair)
        quotes = self._fetch_provider_quotes(pair, benchmark_rate)

        if not quotes:
            raise FXEngineError(f"No FX quotes available for {pair}")

        ranked_routes = self._rank_routes(quotes, amount)
        best = ranked_routes[0]

        # Savings = best net amount minus worst available route (realistic treasury metric)
        savings_usd = best.savings_vs_benchmark_usd
        savings_bps = float(savings_usd / (benchmark_rate * amount) * 10_000) if benchmark_rate and amount else 0.0

        timing = self._recommend_timing(payment, pair)
        hedge = self._detect_hedge_opportunity(pair, float(amount))

        volatility_flag = self._is_high_volatility(pair)

        result = FXResult(
            payment_id=payment.payment_id,
            currency_pair=pair,
            payment_amount=amount,
            benchmark_rate=benchmark_rate,
            quotes=quotes,
            ranked_routes=ranked_routes,
            recommended_provider=best.provider,
            recommended_rate=best.rate,
            estimated_savings_usd=max(savings_usd, Decimal("0")),
            savings_bps=max(savings_bps, 0.0),
            timing_recommendation=timing,
            timing_rationale=self._timing_rationale(timing, pair),
            hedge_opportunity=hedge,
            volatility_flag=volatility_flag,
        )

        logger.info(
            "FX analysis complete",
            payment_id=payment.payment_id,
            recommended_provider=best.provider,
            recommended_rate=str(best.rate),
            savings_usd=str(result.estimated_savings_usd),
        )
        return result

    # ── Rate fetching ─────────────────────────────────────────────────────────

    def _get_benchmark_rate(self, pair: str) -> Decimal:
        rates = self._fx_data.get("rates", {})
        rate = rates.get(pair) or rates.get(pair.replace("/", ""))
        if rate is None:
            # Try inverse
            parts = pair.split("/")
            if len(parts) == 2:
                inv_pair = f"{parts[1]}/{parts[0]}"
                inv_rate = rates.get(inv_pair)
                if inv_rate:
                    return (Decimal("1") / Decimal(str(inv_rate))).quantize(_CENTS)
            return Decimal("1")
        return Decimal(str(rate))

    def _fetch_provider_quotes(self, pair: str, benchmark: Decimal) -> list[RateQuote]:
        """Simulate 3 bank providers with small spread variations around benchmark."""
        providers = [
            {"name": "HSBC Global FX", "spread_bps": 15, "fee_usd": 25},
            {"name": "JP Morgan Treasury", "spread_bps": 12, "fee_usd": 35},
            {"name": "Deutsche Bank FX", "spread_bps": 18, "fee_usd": 20},
        ]
        quotes: list[RateQuote] = []
        for p in providers:
            spread_fraction = Decimal(str(p["spread_bps"])) / Decimal("10000")
            # Simulate slight randomness (±3 bps) for realism
            noise = Decimal(str(random.uniform(-0.0003, 0.0003)))
            bid = (benchmark - spread_fraction / 2 + noise).quantize(_CENTS)
            ask = (benchmark + spread_fraction / 2 + noise).quantize(_CENTS)
            quotes.append(
                RateQuote(
                    provider=p["name"],
                    spot_rate=benchmark,
                    bid=bid,
                    ask=ask,
                    spread_bps=float(p["spread_bps"]),
                    transaction_fee_usd=Decimal(str(p["fee_usd"])),
                )
            )
        return quotes

    # ── Route ranking ─────────────────────────────────────────────────────────

    def _rank_routes(self, quotes: list[RateQuote], amount: Decimal) -> list[FXRoute]:
        routes: list[FXRoute] = []
        for i, q in enumerate(quotes):
            gross = (q.bid * amount).quantize(_CENTS)
            fee = q.transaction_fee_usd
            net = (gross - fee).quantize(_CENTS)
            routes.append(
                FXRoute(
                    rank=i + 1,
                    provider=q.provider,
                    rate=q.bid,
                    gross_amount_target=gross,
                    transaction_fee_usd=fee,
                    net_amount_target=net,
                    total_cost_usd=fee,
                    savings_vs_benchmark_usd=Decimal("0"),
                )
            )
        # Sort by best net amount (highest net = cheapest for payer)
        routes.sort(key=lambda r: r.net_amount_target, reverse=True)
        for rank, route in enumerate(routes, start=1):
            object.__setattr__(route, "rank", rank) if hasattr(route, "__slots__") else setattr(route, "rank", rank)

        # Calculate savings vs worst route
        if len(routes) > 1:
            worst_net = routes[-1].net_amount_target
            for route in routes:
                savings = (route.net_amount_target - worst_net).quantize(_CENTS)
                route.savings_vs_benchmark_usd = max(savings, Decimal("0"))

        return routes

    # ── Timing recommendation ─────────────────────────────────────────────────

    def _recommend_timing(self, payment: PaymentRecord, pair: str) -> FXTimingRecommendation:
        if payment.urgency == PaymentUrgency.SAME_DAY:
            return FXTimingRecommendation.EXECUTE_NOW
        if self._is_high_volatility(pair):
            return FXTimingRecommendation.HEDGE_RECOMMENDED
        trend = self._fx_data.get("trends", {}).get(pair, "STABLE")
        if trend == "IMPROVING" and payment.urgency == PaymentUrgency.FLEXIBLE:
            return FXTimingRecommendation.DEFER_24H
        return FXTimingRecommendation.EXECUTE_NOW

    def _timing_rationale(self, timing: FXTimingRecommendation, pair: str) -> str:
        rationales = {
            FXTimingRecommendation.EXECUTE_NOW: f"{pair} rate is near 30-day average. Execute immediately.",
            FXTimingRecommendation.DEFER_24H: f"{pair} shows improving trend — deferring 24h may reduce cost.",
            FXTimingRecommendation.DEFER_48H: f"{pair} expected to improve over 48h based on forward curve.",
            FXTimingRecommendation.HEDGE_RECOMMENDED: f"{pair} volatility is elevated. Forward hedge recommended.",
        }
        return rationales.get(timing, "")

    def _detect_hedge_opportunity(self, pair: str, amount: float) -> HedgeOpportunity | None:
        if amount >= 500_000 and self._is_high_volatility(pair):
            return HedgeOpportunity(
                hedge_type="FORWARD_CONTRACT",
                description=f"Lock in today's {pair} rate for 30 days via forward contract.",
                estimated_protection_bps=45.0,
                recommended=True,
            )
        return None

    def _is_high_volatility(self, pair: str) -> bool:
        vol_data = self._fx_data.get("volatility", {})
        vol = vol_data.get(pair, 0.0)
        return float(vol) > 0.08

    # ── Data loading ──────────────────────────────────────────────────────────

    @staticmethod
    def _load_default_rates() -> dict[str, Any]:
        path = settings.sample_data_dir / "fx_rates.json"
        if path.exists():
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        logger.warning("FX rates file not found, using fallback 1:1", path=str(path))
        return {"rates": {}, "trends": {}, "volatility": {}}
