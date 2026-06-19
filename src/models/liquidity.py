"""Liquidity and cash position models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LiquidityStatus(str, Enum):
    SUFFICIENT = "SUFFICIENT"
    CONSTRAINED = "CONSTRAINED"
    INSUFFICIENT = "INSUFFICIENT"
    NETTING_AVAILABLE = "NETTING_AVAILABLE"


class CashPosition(BaseModel):
    entity: str
    account_id: str
    currency: str
    available_balance: Decimal
    total_balance: Decimal
    covenant_minimum: Decimal = Decimal("0")
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    @property
    def headroom(self) -> Decimal:
        return self.available_balance - self.covenant_minimum

    @property
    def covenant_breached(self) -> bool:
        return self.available_balance < self.covenant_minimum


class NettingOpportunity(BaseModel):
    offsetting_payment_id: str
    counterparty: str
    currency: str
    offsetting_amount: Decimal
    net_exposure: Decimal
    estimated_fx_saving_usd: Decimal
    description: str = ""


class FundingOption(BaseModel):
    source_entity: str
    source_account: str
    available_amount: Decimal
    currency: str
    funding_type: str
    estimated_cost_usd: Decimal = Decimal("0")
    description: str = ""


class LiquidityResult(BaseModel):
    payment_id: str
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)

    status: LiquidityStatus
    source_position: CashPosition

    post_payment_balance: Decimal
    post_payment_headroom: Decimal
    covenant_at_risk: bool

    netting_opportunity: Optional[NettingOpportunity] = None
    funding_options: list[FundingOption] = Field(default_factory=list)

    recommended_action: str = ""
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)
