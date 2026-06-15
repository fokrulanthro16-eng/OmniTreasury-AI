"""Mock banking API — simulates payment instruction submission and confirmation."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from src.core.logging_config import get_logger
from src.models.payment import PaymentRecord

logger = get_logger("mock_banking_api")


class MockBankingAPIClient:
    """Simulates bank payment instruction submission for demo and integration testing."""

    def __init__(self) -> None:
        self._submitted: dict[str, dict] = {}
        logger.info("MockBankingAPIClient ready")

    def submit_payment(
        self,
        payment: PaymentRecord,
        fx_provider: str,
        execution_rate: Decimal,
    ) -> str:
        """Submit a payment instruction to the mock bank API.

        Returns:
            Bank confirmation reference number.
        """
        confirmation_ref = f"CONF-{uuid.uuid4().hex[:10].upper()}"
        target_amount = (payment.amount * execution_rate).quantize(Decimal("0.01"))

        record = {
            "confirmation_ref": confirmation_ref,
            "payment_id": payment.payment_id,
            "fx_provider": fx_provider,
            "source_amount": str(payment.amount),
            "source_currency": payment.source_currency,
            "target_amount": str(target_amount),
            "target_currency": payment.target_currency,
            "execution_rate": str(execution_rate),
            "counterparty": payment.counterparty.name,
            "submitted_at": datetime.utcnow().isoformat(),
            "status": "SUBMITTED",
        }
        self._submitted[confirmation_ref] = record

        logger.info(
            "[MOCK] Payment submitted to bank",
            confirmation_ref=confirmation_ref,
            payment_id=payment.payment_id,
            source=f"{payment.amount} {payment.source_currency}",
            target=f"{target_amount} {payment.target_currency}",
            fx_provider=fx_provider,
        )
        return confirmation_ref

    def get_payment_status(self, confirmation_ref: str) -> dict:
        """Retrieve the current status of a submitted payment."""
        record = self._submitted.get(confirmation_ref)
        if not record:
            return {"status": "NOT_FOUND", "confirmation_ref": confirmation_ref}
        return record
