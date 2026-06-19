"""Mock ERP integration — simulates SAP TRM / Oracle Treasury data feeds."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from src.core.config import settings
from src.core.logging_config import get_logger
from src.models.payment import CounterpartyDetails, PaymentPurpose, PaymentRecord, PaymentUrgency

logger = get_logger("mock_erp")


class MockERPClient:
    """Loads and serves synthetic treasury payment data as if from a live ERP system."""

    def __init__(self) -> None:
        self._data = self._load_payments()
        logger.info("MockERPClient ready", payment_count=len(self._data))

    def get_pending_payments(self) -> list[PaymentRecord]:
        """Return all pending payment records from mock ERP."""
        records: list[PaymentRecord] = []
        for raw in self._data:
            try:
                records.append(self._to_payment_record(raw))
            except Exception as exc:
                logger.error("Failed to parse ERP record", record_id=raw.get("payment_id"), error=str(exc))
        return records

    def get_payment_by_id(self, payment_id: str) -> PaymentRecord | None:
        """Retrieve a single payment by ID."""
        for raw in self._data:
            if raw.get("payment_id") == payment_id:
                return self._to_payment_record(raw)
        return None

    def get_payment_by_scenario(self, scenario: str) -> PaymentRecord | None:
        """Retrieve first payment matching a scenario tag (useful for demos)."""
        for raw in self._data:
            if raw.get("scenario", "").upper() == scenario.upper():
                return self._to_payment_record(raw)
        return None

    # ── Data mapping ──────────────────────────────────────────────────────────

    @staticmethod
    def _to_payment_record(raw: dict[str, Any]) -> PaymentRecord:
        from datetime import date as _date
        counterparty_raw = raw["counterparty"]
        return PaymentRecord(
            payment_id=raw["payment_id"],
            source_entity=raw["source_entity"],
            source_account=raw["source_account"],
            source_currency=raw["source_currency"],
            amount=Decimal(str(raw["amount"])),
            target_currency=raw["target_currency"],
            counterparty=CounterpartyDetails(
                name=counterparty_raw["name"],
                account_number=counterparty_raw["account_number"],
                bank_name=counterparty_raw["bank_name"],
                bank_swift_code=counterparty_raw["bank_swift_code"],
                bank_country=counterparty_raw["bank_country"],
                is_internal=counterparty_raw.get("is_internal", False),
            ),
            value_date=_date.fromisoformat(raw["value_date"]),
            purpose=PaymentPurpose(raw["purpose"]),
            reference=raw["reference"],
            urgency=PaymentUrgency(raw.get("urgency", "T_PLUS_2")),
            invoice_reference=raw.get("invoice_reference"),
            submitted_by=raw.get("submitted_by"),
            scenario=raw.get("scenario"),
        )

    def _load_payments(self) -> list[dict[str, Any]]:
        path = settings.sample_data_dir / "payments.json"
        if path.exists():
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        logger.warning("Payments file not found", path=str(path))
        return []
