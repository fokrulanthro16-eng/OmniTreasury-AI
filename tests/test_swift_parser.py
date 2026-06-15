"""Unit tests for the SWIFT MT103 parser."""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.parsers.swift_mt103 import parse_mt103, _extract_fields, _parse_32a
from src.core.exceptions import ParseError
from src.models.payment import PaymentPurpose


SAMPLE_MT103 = """{1:F01DEUTDEDBAXXX0000000000}{2:I103BARCGB2LXXXXN}{4:
:20:20240115REF001
:23B:CRED
:32A:240115EUR45000,00
:50K:/DE89370400440532013000
ACME CORPORATION GmbH
Hauptstrasse 1
Berlin
:52A:DEUTDEDB
:53B:/DE89370400440532013000
:57A:BARCGB22
:59:/GB29NWBK60161331926819
GLOBAL VENTURES LTD
15 LONDON BRIDGE STREET
LONDON SE1 9SG
:70:INVOICE 2024-001 TRADE PAYMENT
:71A:OUR
:72:/ACC/MONTHLY PAYMENT
-}"""

MINIMAL_MT103 = """:20:MINREF001
:23B:CRED
:32A:260614USD100000,00
:59:/US12345678
BENEFICIARY CORP"""


class TestMT103Parsing:
    def test_parse_full_message_returns_payment_record(self) -> None:
        payment = parse_mt103(SAMPLE_MT103)
        assert payment is not None
        assert payment.amount == Decimal("45000.00")
        assert payment.source_currency == "EUR"

    def test_reference_extracted_correctly(self) -> None:
        payment = parse_mt103(SAMPLE_MT103)
        assert payment.reference == "20240115REF001"

    def test_counterparty_name_extracted(self) -> None:
        payment = parse_mt103(SAMPLE_MT103)
        assert "GLOBAL VENTURES" in payment.counterparty.name.upper()

    def test_bank_swift_code_extracted(self) -> None:
        payment = parse_mt103(SAMPLE_MT103)
        assert payment.counterparty.bank_swift_code == "BARCGB22"

    def test_source_entity_preserved(self) -> None:
        payment = parse_mt103(SAMPLE_MT103, source_entity="EMEA-HQ")
        assert payment.source_entity == "EMEA-HQ"

    def test_trade_payment_purpose_inferred(self) -> None:
        payment = parse_mt103(SAMPLE_MT103)
        assert payment.purpose == PaymentPurpose.TRADE_PAYMENT

    def test_minimal_message_parsed(self) -> None:
        payment = parse_mt103(MINIMAL_MT103)
        assert payment.amount == Decimal("100000.00")
        assert payment.source_currency == "USD"

    def test_missing_32a_raises_parse_error(self) -> None:
        bad_message = ":20:REF001\n:23B:CRED\n:59:/ACC\nBENE CORP"
        with pytest.raises(ParseError):
            parse_mt103(bad_message)


class TestFieldExtraction:
    def test_extract_fields_returns_dict(self) -> None:
        body = ":20:REF001\n:32A:240115EUR45000,00\n:59:/ACC\nBENE"
        fields = _extract_fields(body)
        assert "20" in fields
        assert "32A" in fields
        assert fields["20"] == "REF001"

    def test_parse_32a_returns_tuple(self) -> None:
        value_date, currency, amount = _parse_32a("240115EUR45000,00")
        assert currency == "EUR"
        assert amount == Decimal("45000.00")
        assert value_date.year == 2024
        assert value_date.month == 1
        assert value_date.day == 15

    def test_parse_32a_invalid_raises_parse_error(self) -> None:
        with pytest.raises(ParseError):
            _parse_32a("INVALID")


class TestPurposeInference:
    def test_invoice_keyword_maps_to_trade(self) -> None:
        payment = parse_mt103(SAMPLE_MT103)
        assert payment.purpose == PaymentPurpose.TRADE_PAYMENT

    def test_no_remittance_maps_to_other(self) -> None:
        msg = ":20:REF\n:32A:260614USD5000,00\n:59:/ACC\nBENE CORP"
        payment = parse_mt103(msg)
        assert payment.purpose == PaymentPurpose.OTHER
