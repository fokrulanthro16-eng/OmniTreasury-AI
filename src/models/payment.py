"""Payment domain models."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    IN_ANALYSIS = "IN_ANALYSIS"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"
    ESCALATED = "ESCALATED"
    BLOCKED = "BLOCKED"


class PaymentUrgency(str, Enum):
    SAME_DAY = "SAME_DAY"
    T_PLUS_1 = "T_PLUS_1"
    T_PLUS_2 = "T_PLUS_2"
    FLEXIBLE = "FLEXIBLE"


class PaymentPurpose(str, Enum):
    TRADE_PAYMENT = "TRADE_PAYMENT"
    INTERCOMPANY_TRANSFER = "INTERCOMPANY_TRANSFER"
    DIVIDEND = "DIVIDEND"
    LOAN_REPAYMENT = "LOAN_REPAYMENT"
    SALARY = "SALARY"
    TAX = "TAX"
    SERVICES = "SERVICES"
    OTHER = "OTHER"


class CounterpartyDetails(BaseModel):
    name: str
    account_number: str
    bank_name: str
    bank_swift_code: str
    bank_country: str
    address: Optional[str] = None
    entity_id: Optional[str] = None
    is_internal: bool = False


class PaymentRecord(BaseModel):
    payment_id: str = Field(default_factory=lambda: f"PAY-{uuid.uuid4().hex[:8].upper()}")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Core payment details
    source_entity: str
    source_account: str
    source_currency: str

    amount: Decimal
    target_currency: str

    counterparty: CounterpartyDetails

    value_date: date
    purpose: PaymentPurpose
    reference: str

    urgency: PaymentUrgency = PaymentUrgency.T_PLUS_2
    status: PaymentStatus = PaymentStatus.PENDING

    # Optional enrichment
    invoice_reference: Optional[str] = None
    swift_message: Optional[str] = None
    internal_notes: Optional[str] = None
    submitted_by: Optional[str] = None
    scenario: Optional[str] = None

    @field_validator("source_currency", "target_currency")
    @classmethod
    def normalise_currency(cls, v: str) -> str:
        return v.upper().strip()

    @property
    def is_cross_border(self) -> bool:
        return self.source_currency != self.target_currency

    @property
    def currency_pair(self) -> str:
        return f"{self.source_currency}/{self.target_currency}"

    def model_post_init(self, __context: object) -> None:
        self.status = PaymentStatus.PENDING
