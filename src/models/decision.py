"""Decision orchestration models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .compliance import ComplianceResult
from .forex import FXResult
from .liquidity import LiquidityResult
from .risk import RiskResult


class DecisionType(str, Enum):
    AUTO_EXECUTE = "AUTO_EXECUTE"
    ESCALATE = "ESCALATE"
    HARD_REJECT = "HARD_REJECT"


class EscalationLevel(str, Enum):
    COMPLIANCE_OFFICER = "COMPLIANCE_OFFICER"
    TREASURY_MANAGER = "TREASURY_MANAGER"
    CFO = "CFO"
    LEGAL = "LEGAL"


class DecisionRationale(BaseModel):
    trigger: str
    description: str
    agent_source: str


class CasePayload(BaseModel):
    """Structured payload attached to a Maestro Case on escalation."""
    case_title: str
    case_type: str
    priority: str
    assigned_role: EscalationLevel
    sla_minutes: int

    payment_summary: dict = Field(default_factory=dict)
    compliance_report: dict = Field(default_factory=dict)
    risk_report: dict = Field(default_factory=dict)
    fx_analysis: dict = Field(default_factory=dict)
    liquidity_status: dict = Field(default_factory=dict)
    agent_recommendations: list[str] = Field(default_factory=list)


class DecisionResult(BaseModel):
    payment_id: str
    decided_at: datetime = Field(default_factory=datetime.utcnow)

    decision: DecisionType
    escalation_level: Optional[EscalationLevel] = None

    rationales: list[DecisionRationale] = Field(default_factory=list)
    execution_route: Optional[str] = None

    case_payload: Optional[CasePayload] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    summary: str = ""

    # Agent input snapshots
    compliance_result: Optional[ComplianceResult] = None
    fx_result: Optional[FXResult] = None
    liquidity_result: Optional[LiquidityResult] = None
    risk_result: Optional[RiskResult] = None
