"""Compliance result models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ComplianceDecision(str, Enum):
    CLEAR = "CLEAR"
    FLAG = "FLAG"
    BLOCK = "BLOCK"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SanctionsMatch(BaseModel):
    matched_name: str
    input_name: str
    similarity_score: float
    list_type: str
    reason: str = ""
    is_exact: bool = False
    entity_id: Optional[str] = None

    @property
    def is_high_confidence(self) -> bool:
        return self.similarity_score >= 90


class JurisdictionRisk(BaseModel):
    country: str
    level: RiskLevel
    list_type: Optional[str] = None
    description: str = ""


class AMLFlag(BaseModel):
    flag_type: str
    description: str
    severity: RiskLevel
    evidence: dict = Field(default_factory=dict)


class ComplianceResult(BaseModel):
    payment_id: str
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)

    decision: ComplianceDecision
    confidence: float = Field(ge=0.0, le=1.0)

    sanctions_matches: list[SanctionsMatch] = Field(default_factory=list)
    jurisdiction_risks: list[JurisdictionRisk] = Field(default_factory=list)
    aml_flags: list[AMLFlag] = Field(default_factory=list)

    policy_references: list[str] = Field(default_factory=list)
    recommended_approver: Optional[str] = None
    summary: str = ""

    @property
    def has_sanctions_hit(self) -> bool:
        return len(self.sanctions_matches) > 0

    @property
    def highest_jurisdiction_risk(self) -> RiskLevel:
        if not self.jurisdiction_risks:
            return RiskLevel.LOW
        levels = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        return max(self.jurisdiction_risks, key=lambda j: levels.index(j.level)).level
