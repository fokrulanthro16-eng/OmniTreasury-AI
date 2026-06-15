"""SWIFT MT103 Single Customer Credit Transfer parser.

Handles standard ISO 15022 field tags extracted from raw MT103 message text.
Produces a normalised PaymentRecord for pipeline ingestion.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from src.core.exceptions import ParseError
from src.core.logging_config import get_logger
from src.models.payment import (
    CounterpartyDetails,
    PaymentPurpose,
    PaymentRecord,
    PaymentUrgency,
)

logger = get_logger("swift_mt103_parser")

# Maps MT103 field tag → field name used in parsed output
_FIELD_TAGS = {
    "20": "transaction_reference",
    "23B": "bank_operation_code",
    "32A": "value_date_currency_amount",
    "33B": "currency_instructed_amount",
    "50K": "ordering_customer",
    "50A": "ordering_customer_bic",
    "52A": "ordering_institution_bic",
    "53B": "senders_correspondent",
    "56A": "intermediary_institution",
    "57A": "account_with_institution",
    "59": "beneficiary_customer",
    "70": "remittance_information",
    "71A": "details_of_charges",
    "72": "sender_to_receiver_info",
}

_CURRENCY_TO_PURPOSE: dict[str, PaymentPurpose] = {}


def _strip_block_headers(raw: str) -> str:
    """Remove SWIFT block wrappers {1:...}{2:...}{4: ... -}."""
    match = re.search(r"\{4:(.*?)-\}", raw, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Already stripped or non-standard — return as-is
    return raw.strip()


def _extract_fields(body: str) -> dict[str, str]:
    """Split MT103 body into {tag: value} pairs."""
    fields: dict[str, str] = {}
    pattern = re.compile(r":(\d{2}[A-Z]?):(.*?)(?=:\d{2}[A-Z]?:|$)", re.DOTALL)
    for match in pattern.finditer(body):
        tag = match.group(1).strip()
        value = match.group(2).strip()
        fields[tag] = value
    return fields


def _parse_32a(raw: str) -> tuple[date, str, Decimal]:
    """Parse field :32A: → (value_date, currency, amount).

    Format: YYMMDDCCCNNN,NN
    Example: 240115EUR45000,00
    """
    raw = raw.strip()
    if len(raw) < 10:
        raise ParseError(f"Field 32A too short to parse: '{raw}'")

    date_str = raw[:6]
    currency = raw[6:9].upper()
    amount_str = raw[9:].replace(",", ".")

    try:
        value_date = datetime.strptime(date_str, "%y%m%d").date()
    except ValueError as exc:
        raise ParseError(f"Cannot parse date from 32A '{date_str}': {exc}") from exc

    try:
        amount = Decimal(amount_str)
    except InvalidOperation as exc:
        raise ParseError(f"Cannot parse amount from 32A '{amount_str}': {exc}") from exc

    return value_date, currency, amount


def _parse_account_and_name(raw: str) -> tuple[Optional[str], str]:
    """Parse /ACCOUNT\nNAME\nADDRESS blocks common in 50K / 59 fields."""
    lines = [l.strip() for l in raw.strip().splitlines() if l.strip()]
    account: Optional[str] = None
    name_parts: list[str] = []

    for line in lines:
        if line.startswith("/") and account is None:
            account = line.lstrip("/")
        else:
            name_parts.append(line)

    name = name_parts[0] if name_parts else "UNKNOWN"
    return account, name


def _parse_57a_bic(raw: str) -> tuple[Optional[str], str]:
    """Parse :57A: field → (account, BIC/bank name)."""
    lines = [l.strip() for l in raw.strip().splitlines() if l.strip()]
    account: Optional[str] = None
    bic: str = "UNKNOWN"
    for line in lines:
        if line.startswith("/"):
            account = line.lstrip("/")
        else:
            bic = line
    return account, bic


def parse_mt103(raw_message: str, source_entity: str = "CORP-HQ") -> PaymentRecord:
    """Parse a raw SWIFT MT103 string into a PaymentRecord.

    Args:
        raw_message: Full MT103 text (with or without block headers).
        source_entity: Internal entity name that submitted the payment.

    Returns:
        A validated PaymentRecord ready for pipeline ingestion.

    Raises:
        ParseError: If mandatory fields are missing or malformed.
    """
    logger.info("Parsing MT103 message", source_entity=source_entity)

    body = _strip_block_headers(raw_message)
    fields = _extract_fields(body)

    logger.debug("Extracted MT103 fields", tags=list(fields.keys()))

    # ── Mandatory field :32A: ────────────────────────────────────────────────
    if "32A" not in fields:
        raise ParseError("Mandatory field :32A: (value date/currency/amount) is missing.")

    value_date, source_currency, amount = _parse_32a(fields["32A"])

    # ── Transaction reference :20: ───────────────────────────────────────────
    reference = fields.get("20", f"MT103-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}")

    # ── Ordering customer :50K: → source account ─────────────────────────────
    source_account: str = "ACCOUNT-UNKNOWN"
    if "50K" in fields:
        acc, _ = _parse_account_and_name(fields["50K"])
        if acc:
            source_account = acc
    elif "50A" in fields:
        source_account = fields["50A"].strip().lstrip("/")

    # ── Beneficiary :59: → counterparty ──────────────────────────────────────
    ben_account: Optional[str] = None
    ben_name: str = "BENEFICIARY UNKNOWN"
    if "59" in fields:
        ben_account, ben_name = _parse_account_and_name(fields["59"])

    # ── Account-with institution :57A: → counterparty bank ───────────────────
    _, bank_bic = _parse_57a_bic(fields.get("57A", "BANKUNKN"))
    bank_country = bank_bic[4:6] if len(bank_bic) >= 6 else "XX"

    # ── Target currency: from :33B: if present, else same as 32A ─────────────
    target_currency = source_currency
    if "33B" in fields:
        raw_33b = fields["33B"].strip()
        if len(raw_33b) >= 3:
            target_currency = raw_33b[:3].upper()

    # ── Remittance info :70: → purpose ───────────────────────────────────────
    remittance_info = fields.get("70", "")
    purpose = _infer_purpose(remittance_info)

    counterparty = CounterpartyDetails(
        name=ben_name,
        account_number=ben_account or "UNKNOWN",
        bank_name=bank_bic,
        bank_swift_code=bank_bic,
        bank_country=bank_country,
    )

    record = PaymentRecord(
        source_entity=source_entity,
        source_account=source_account,
        source_currency=source_currency,
        amount=amount,
        target_currency=target_currency,
        counterparty=counterparty,
        value_date=value_date,
        purpose=purpose,
        reference=reference,
        urgency=PaymentUrgency.T_PLUS_2,
        swift_message=raw_message,
        internal_notes=remittance_info,
    )

    logger.info(
        "MT103 parsed successfully",
        payment_id=record.payment_id,
        amount=str(amount),
        currency_pair=record.currency_pair,
        counterparty=ben_name,
    )
    return record


def _infer_purpose(remittance_info: str) -> PaymentPurpose:
    """Heuristic purpose mapping from remittance information text."""
    lower = remittance_info.lower()
    if any(kw in lower for kw in ("invoice", "inv", "trade", "goods", "services")):
        return PaymentPurpose.TRADE_PAYMENT
    if any(kw in lower for kw in ("interco", "intercompany", "internal")):
        return PaymentPurpose.INTERCOMPANY_TRANSFER
    if "dividend" in lower:
        return PaymentPurpose.DIVIDEND
    if any(kw in lower for kw in ("loan", "repayment", "principal")):
        return PaymentPurpose.LOAN_REPAYMENT
    if any(kw in lower for kw in ("salary", "payroll", "wages")):
        return PaymentPurpose.SALARY
    if "tax" in lower:
        return PaymentPurpose.TAX
    return PaymentPurpose.OTHER
