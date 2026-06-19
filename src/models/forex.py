"""FX result and routing models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class FXTimingRecommendation(str, Enum):
    EXECUTE_NOW = "EXECUTE_NOW"
    DEFER_24H = "DEFER_24H"
    DEFER_48H = "DEFER_48H"
    HEDGE_RECOMMENDED = "HEDGE_RECOMMENDED"


class RateQuote(BaseModel):
    provider: str
    spot_rate: Decimal
    bid: Decimal
    ask: Decimal
    spread_bps: float
    transaction_fee_usd: Decimal = Decimal("0")
    quoted_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def effective_rate(self) -> Decimal:
        return self.bid


class FXRoute(BaseModel):
    rank: int
    provider: str
    rate: Decimal
    gross_amount_target: Decimal
    transaction_fee_usd: Decimal
    net_amount_target: Decimal
    total_cost_usd: Decimal
    savings_vs_benchmark_usd: Decimal


class HedgeOpportunity(BaseModel):
    hedge_type: str
    description: str
    estimated_protection_bps: float
    recommended: bool = False


class FXResult(BaseModel):
    payment_id: str
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)

    currency_pair: str
    payment_amount: Decimal
    benchmark_rate: Decimal

    quotes: list[RateQuote] = Field(default_factory=list)
    ranked_routes: list[FXRoute] = Field(default_factory=list)

    recommended_provider: str
    recommended_rate: Decimal
    estimated_savings_usd: Decimal
    savings_bps: float

    timing_recommendation: FXTimingRecommendation
    timing_rationale: str = ""

    hedge_opportunity: Optional[HedgeOpportunity] = None
    volatility_flag: bool = False
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)

    @property
    def best_route(self) -> Optional[FXRoute]:
        if not self.ranked_routes:
            return None
        return self.ranked_routes[0]
