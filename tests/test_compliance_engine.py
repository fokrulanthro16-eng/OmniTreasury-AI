"""Unit tests for the ComplianceEngine."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from src.engines.compliance_engine import ComplianceEngine
from src.models.compliance import ComplianceDecision, RiskLevel
from src.models.payment import CounterpartyDetails, PaymentPurpose, PaymentRecord


SANCTIONS_DATA = [
    {"name": "Orion Global Trading LLC", "list_type": "OFAC", "reason": "SDN list", "entity_id": "SDN-001"},
    {"name": "Tehran Import Export Co", "list_type": "UN_CONSOLIDATED", "reason": "Iran nexus", "entity_id": "UN-042"},
    {"name": "Pyongyang Tech Partners", "list_type": "OFAC", "reason": "DPRK affiliation", "entity_id": "SDN-099"},
]


def make_payment(
    counterparty_name: str,
    bank_country: str = "DE",
    amount: float = 45_000.0,
    source_currency: str = "EUR",
) -> PaymentRecord:
    return PaymentRecord(
        source_entity="CORP-HQ",
        source_account="DE89370400440532013000",
        source_currency=source_currency,
        amount=Decimal(str(amount)),
        target_currency=source_currency,
        counterparty=CounterpartyDetails(
            name=counterparty_name,
            account_number="GB29NWBK60161331926819",
            bank_name="Test Bank",
            bank_swift_code="TESTGB2L",
            bank_country=bank_country,
        ),
        value_date=date(2026, 6, 15),
        purpose=PaymentPurpose.TRADE_PAYMENT,
        reference="TEST-001",
    )


@pytest.fixture
def engine() -> ComplianceEngine:
    return ComplianceEngine(sanctions_data=SANCTIONS_DATA)


class TestSanctionsScreening:
    def test_clean_counterparty_returns_clear(self, engine: ComplianceEngine) -> None:
        payment = make_payment("Acme Manufacturing GmbH", bank_country="DE")
        result = engine.run(payment)
        assert result.decision == ComplianceDecision.CLEAR

    def test_exact_sanctions_match_returns_block(self, engine: ComplianceEngine) -> None:
        payment = make_payment("Orion Global Trading LLC", bank_country="AE")
        result = engine.run(payment)
        assert result.decision == ComplianceDecision.BLOCK
        assert result.has_sanctions_hit is True

    def test_fuzzy_sanctions_match_returns_flag(self, engine: ComplianceEngine) -> None:
        payment = make_payment("Orion Global Trading L.L.C", bank_country="AE")
        result = engine.run(payment)
        assert result.decision in (ComplianceDecision.FLAG, ComplianceDecision.BLOCK)

    def test_partial_sanctions_name_flagged(self, engine: ComplianceEngine) -> None:
        payment = make_payment("Tehran Import Export", bank_country="IR")
        result = engine.run(payment)
        assert result.decision in (ComplianceDecision.FLAG, ComplianceDecision.BLOCK)


class TestJurisdictionRisk:
    def test_fatf_blacklist_country_returns_flag(self, engine: ComplianceEngine) -> None:
        payment = make_payment("Legitimate Local Co", bank_country="IR")  # Iran
        result = engine.run(payment)
        assert result.decision in (ComplianceDecision.FLAG, ComplianceDecision.BLOCK)
        assert result.highest_jurisdiction_risk == RiskLevel.CRITICAL

    def test_fatf_greylist_country_flagged(self, engine: ComplianceEngine) -> None:
        payment = make_payment("Normal Corp Ltd", bank_country="PK")  # Pakistan
        result = engine.run(payment)
        assert result.highest_jurisdiction_risk in (RiskLevel.HIGH, RiskLevel.MEDIUM)

    def test_safe_country_no_jurisdiction_flag(self, engine: ComplianceEngine) -> None:
        payment = make_payment("Swiss AG Corp", bank_country="CH")
        result = engine.run(payment)
        assert result.highest_jurisdiction_risk == RiskLevel.LOW


class TestAMLPatterns:
    def test_ctr_threshold_triggers_flag(self, engine: ComplianceEngine) -> None:
        payment = make_payment("Good Corp", bank_country="US", amount=12_000.0)
        result = engine.run(payment)
        aml_types = [f.flag_type for f in result.aml_flags]
        assert "CTR_THRESHOLD" in aml_types

    def test_structuring_amount_triggers_flag(self, engine: ComplianceEngine) -> None:
        payment = make_payment("Good Corp", bank_country="US", amount=9_700.0)
        result = engine.run(payment)
        aml_types = [f.flag_type for f in result.aml_flags]
        assert "STRUCTURING" in aml_types

    def test_normal_amount_no_aml_flag(self, engine: ComplianceEngine) -> None:
        payment = make_payment("Good Corp", bank_country="DE", amount=45_000.0)
        result = engine.run(payment)
        structuring = [f for f in result.aml_flags if f.flag_type == "STRUCTURING"]
        assert len(structuring) == 0


class TestResultStructure:
    def test_result_has_policy_references_on_flag(self, engine: ComplianceEngine) -> None:
        payment = make_payment("Orion Global Trading LLC", bank_country="AE")
        result = engine.run(payment)
        assert len(result.policy_references) > 0

    def test_result_confidence_is_bounded(self, engine: ComplianceEngine) -> None:
        payment = make_payment("Test Corp", bank_country="DE")
        result = engine.run(payment)
        assert 0.0 <= result.confidence <= 1.0

    def test_recommended_approver_set_on_flag(self, engine: ComplianceEngine) -> None:
        payment = make_payment("Orion Global Trading LLC", bank_country="AE")
        result = engine.run(payment)
        assert result.recommended_approver is not None
