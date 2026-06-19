"""Risk assessment and scoring models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskCategory(str, Enum):
    COUNTERPARTY = "COUNTERPARTY"
    CONCENTRATION = "CONCENTRATION"
    MARKET = "MARKET"
    OPERATIONAL = "OPERATIONAL"
    SETTLEMENT = "SETTLEMENT"


class RiskFactor(BaseModel):
    category: RiskCategory
    name: str
    score: float = Field(ge=0.0, le=100.0)
    weight: float = Field(ge=0.0, le=1.0)
    description: str
    level: RiskLevel
    evidence: dict = Field(default_factory=dict)


class ConcentrationCheck(BaseModel):
    dimension: str
    current_exposure: float
    limit: float
    utilisation_pct: float
    breached: bool

    @property
    def headroom_pct(self) -> float:
        return max(0.0, 100.0 - self.utilisation_pct)


class OperationalFlag(BaseModel):
    flag_type: str
    description: str
    severity: RiskLevel


class RiskResult(BaseModel):
    payment_id: str
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)

    composite_score: float = Field(ge=0.0, le=100.0)
    risk_level: RiskLevel

    factors: list[RiskFactor] = Field(default_factory=list)
    concentration_checks: list[ConcentrationCheck] = Field(default_factory=list)
    operational_flags: list[OperationalFlag] = Field(default_factory=list)

    limit_breaches: list[str] = Field(default_factory=list)
    mitigation_recommendations: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)

    @property
    def has_limit_breach(self) -> bool:
        return len(self.limit_breaches) > 0
