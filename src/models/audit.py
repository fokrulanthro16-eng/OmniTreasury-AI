"""Immutable audit trail models."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AuditEvent(str, Enum):
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    DOCUMENT_PARSED = "DOCUMENT_PARSED"
    AGENT_ANALYSIS_STARTED = "AGENT_ANALYSIS_STARTED"
    AGENT_ANALYSIS_COMPLETE = "AGENT_ANALYSIS_COMPLETE"
    AUTO_DECISION = "AUTO_DECISION"
    CASE_CREATED = "CASE_CREATED"
    HUMAN_DECISION = "HUMAN_DECISION"
    PAYMENT_EXECUTED = "PAYMENT_EXECUTED"
    PAYMENT_REJECTED = "PAYMENT_REJECTED"
    PAYMENT_BLOCKED = "PAYMENT_BLOCKED"
    SLA_BREACH = "SLA_BREACH"
    ESCALATION_TIER_CHANGE = "ESCALATION_TIER_CHANGE"
    FILE_UPLOADED = "FILE_UPLOADED"


class AuditRecord(BaseModel):
    record_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    payment_id: str
    event_type: AuditEvent
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    agent_name: Optional[str] = None
    decision: Optional[str] = None
    reasoning_summary: dict = Field(default_factory=dict)
    confidence_score: Optional[float] = None

    human_approver: Optional[str] = None
    human_notes: Optional[str] = None
    case_id: Optional[str] = None

    policy_references: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

    model_config = {"frozen": True}
