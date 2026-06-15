"""Compliance engine: sanctions screening, AML detection, jurisdiction risk.

All checks are grounded in structured reference data loaded from Data Service
(or sample_data in mock mode). No LLM hallucination of financial facts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fuzzywuzzy import fuzz

from src.core.config import settings
from src.core.exceptions import ComplianceError
from src.core.logging_config import get_logger
from src.models.compliance import (
    AMLFlag,
    ComplianceDecision,
    ComplianceResult,
    JurisdictionRisk,
    RiskLevel,
    SanctionsMatch,
)
from src.models.payment import PaymentRecord

logger = get_logger("compliance_engine")

# FATF jurisdiction risk mapping (ISO country codes)
_FATF_BLACKLIST: frozenset[str] = frozenset({"IR", "KP", "MM"})  # Iran, DPRK, Myanmar
_FATF_GREYLIST: frozenset[str] = frozenset({"PK", "AE", "NG", "ET", "ZA", "SY", "YE", "LY"})

# CTR threshold (USD equivalent) for AML reporting flags
_CTR_THRESHOLD_USD = 10_000.0
_SAR_STRUCTURING_THRESHOLD = 9_500.0


class ComplianceEngine:
    """Evaluates a payment against sanctions lists, AML rules, and jurisdiction policy."""

    def __init__(self, sanctions_data: list[dict[str, Any]] | None = None) -> None:
        self._sanctions = sanctions_data or self._load_default_sanctions()
        logger.info("ComplianceEngine initialised", sanctions_entries=len(self._sanctions))

    # ── Public interface ──────────────────────────────────────────────────────

    def run(self, payment: PaymentRecord) -> ComplianceResult:
        """Run all compliance checks and return a consolidated result."""
        logger.info("Running compliance check", payment_id=payment.payment_id)

        sanctions_matches = self._screen_sanctions(
            payment.counterparty.name,
            payment.counterparty.bank_country,
        )
        jurisdiction_risks = self._assess_jurisdictions(
            payment.counterparty.bank_country
        )
        aml_flags = self._detect_aml_patterns(payment)

        decision, confidence = self._determine_decision(
            sanctions_matches, jurisdiction_risks, aml_flags
        )

        policy_refs = self._collect_policy_references(
            sanctions_matches, jurisdiction_risks, aml_flags
        )
        approver = self._recommend_approver(decision, sanctions_matches)

        summary = self._build_summary(
            decision, sanctions_matches, jurisdiction_risks, aml_flags
        )

        result = ComplianceResult(
            payment_id=payment.payment_id,
            decision=decision,
            confidence=confidence,
            sanctions_matches=sanctions_matches,
            jurisdiction_risks=jurisdiction_risks,
            aml_flags=aml_flags,
            policy_references=policy_refs,
            recommended_approver=approver,
            summary=summary,
        )
        logger.info(
            "Compliance check complete",
            payment_id=payment.payment_id,
            decision=decision.value,
            sanctions_hits=len(sanctions_matches),
        )
        return result

    # ── Sanctions screening ───────────────────────────────────────────────────

    def _screen_sanctions(self, name: str, country: str) -> list[SanctionsMatch]:
        matches: list[SanctionsMatch] = []
        threshold = settings.compliance_fuzzy_match_threshold
        name_upper = name.upper().strip()

        for entry in self._sanctions:
            listed_name = entry.get("name", "").upper().strip()
            if not listed_name:
                continue

            score = fuzz.ratio(name_upper, listed_name)
            token_score = fuzz.token_set_ratio(name_upper, listed_name)
            best_score = max(score, token_score)

            if best_score >= threshold:
                matches.append(
                    SanctionsMatch(
                        matched_name=entry["name"],
                        input_name=name,
                        similarity_score=float(best_score),
                        list_type=entry.get("list_type", "UNKNOWN"),
                        reason=entry.get("reason", "Listed entity"),
                        is_exact=best_score >= 95,
                        entity_id=entry.get("entity_id"),
                    )
                )
                logger.warning(
                    "Sanctions match detected",
                    input_name=name,
                    matched=entry["name"],
                    score=best_score,
                )
        return matches

    # ── Jurisdiction risk ─────────────────────────────────────────────────────

    def _assess_jurisdictions(self, country: str) -> list[JurisdictionRisk]:
        risks: list[JurisdictionRisk] = []
        code = country.upper()[:2]

        if code in _FATF_BLACKLIST:
            risks.append(
                JurisdictionRisk(
                    country=country,
                    level=RiskLevel.CRITICAL,
                    list_type="FATF_BLACKLIST",
                    description=f"{country} is on the FATF high-risk blacklist. Payment requires mandatory review.",
                )
            )
        elif code in _FATF_GREYLIST:
            risks.append(
                JurisdictionRisk(
                    country=country,
                    level=RiskLevel.HIGH,
                    list_type="FATF_GREYLIST",
                    description=f"{country} is under enhanced FATF monitoring (grey list).",
                )
            )
        return risks

    # ── AML pattern detection ─────────────────────────────────────────────────

    def _detect_aml_patterns(self, payment: PaymentRecord) -> list[AMLFlag]:
        flags: list[AMLFlag] = []
        amount_float = float(payment.amount)

        # Structuring: amount just below CTR threshold
        if _SAR_STRUCTURING_THRESHOLD <= amount_float < _CTR_THRESHOLD_USD:
            flags.append(
                AMLFlag(
                    flag_type="STRUCTURING",
                    description=(
                        f"Payment amount {amount_float:,.2f} is between "
                        f"${_SAR_STRUCTURING_THRESHOLD:,.0f} and ${_CTR_THRESHOLD_USD:,.0f} — "
                        "potential structuring to avoid CTR filing."
                    ),
                    severity=RiskLevel.HIGH,
                    evidence={"amount": amount_float, "threshold": _CTR_THRESHOLD_USD},
                )
            )

        # CTR threshold exceeded
        if amount_float >= _CTR_THRESHOLD_USD:
            flags.append(
                AMLFlag(
                    flag_type="CTR_THRESHOLD",
                    description=f"Amount {amount_float:,.2f} exceeds CTR reporting threshold of ${_CTR_THRESHOLD_USD:,.0f}.",
                    severity=RiskLevel.MEDIUM,
                    evidence={"amount": amount_float},
                )
            )

        # Round-number large amount flag
        if amount_float >= 50_000 and amount_float % 10_000 == 0:
            flags.append(
                AMLFlag(
                    flag_type="ROUND_AMOUNT",
                    description=f"Payment is a large round number ({amount_float:,.0f}) — AML monitoring flag.",
                    severity=RiskLevel.LOW,
                    evidence={"amount": amount_float},
                )
            )

        return flags

    # ── Decision logic ────────────────────────────────────────────────────────

    def _determine_decision(
        self,
        sanctions_matches: list[SanctionsMatch],
        jurisdiction_risks: list[JurisdictionRisk],
        aml_flags: list[AMLFlag],
    ) -> tuple[ComplianceDecision, float]:
        # Exact sanctions match → BLOCK
        if any(m.is_exact for m in sanctions_matches):
            return ComplianceDecision.BLOCK, 0.99

        # High-confidence sanctions match → FLAG
        if any(m.is_high_confidence for m in sanctions_matches):
            return ComplianceDecision.FLAG, 0.90

        # Any sanctions match → FLAG
        if sanctions_matches:
            return ComplianceDecision.FLAG, 0.80

        # FATF blacklist jurisdiction → FLAG
        if any(j.level == RiskLevel.CRITICAL for j in jurisdiction_risks):
            return ComplianceDecision.FLAG, 0.95

        # FATF greylist → FLAG
        if any(j.level == RiskLevel.HIGH for j in jurisdiction_risks):
            return ComplianceDecision.FLAG, 0.85

        # High-severity AML flag → FLAG
        if any(f.severity in (RiskLevel.HIGH, RiskLevel.CRITICAL) for f in aml_flags):
            return ComplianceDecision.FLAG, 0.80

        return ComplianceDecision.CLEAR, 0.97

    # ── Supporting helpers ────────────────────────────────────────────────────

    def _recommend_approver(
        self,
        decision: ComplianceDecision,
        sanctions_matches: list[SanctionsMatch],
    ) -> str | None:
        if decision == ComplianceDecision.BLOCK:
            return "LEGAL"
        if decision == ComplianceDecision.FLAG:
            if any(m.list_type in ("OFAC", "UN_CONSOLIDATED") for m in sanctions_matches):
                return "LEGAL"
            return "COMPLIANCE_OFFICER"
        return None

    def _collect_policy_references(
        self,
        sanctions_matches: list[SanctionsMatch],
        jurisdiction_risks: list[JurisdictionRisk],
        aml_flags: list[AMLFlag],
    ) -> list[str]:
        refs: list[str] = []
        if sanctions_matches:
            refs += ["OFAC Sanctions Regulations 31 CFR Part 500", "UN Security Council Resolutions"]
        if any(j.list_type == "FATF_BLACKLIST" for j in jurisdiction_risks):
            refs.append("FATF Recommendation 19 — Higher Risk Countries")
        if any(j.list_type == "FATF_GREYLIST" for j in jurisdiction_risks):
            refs.append("FATF Monitoring Process — Enhanced Due Diligence")
        if any(f.flag_type == "CTR_THRESHOLD" for f in aml_flags):
            refs.append("Bank Secrecy Act — 31 CFR 103.22 Currency Transaction Report")
        if any(f.flag_type == "STRUCTURING" for f in aml_flags):
            refs.append("Bank Secrecy Act — 31 USC 5324 Anti-Structuring")
        return list(set(refs))

    def _build_summary(
        self,
        decision: ComplianceDecision,
        sanctions_matches: list[SanctionsMatch],
        jurisdiction_risks: list[JurisdictionRisk],
        aml_flags: list[AMLFlag],
    ) -> str:
        parts: list[str] = [f"Decision: {decision.value}."]
        if sanctions_matches:
            top = sanctions_matches[0]
            parts.append(
                f"Sanctions: {len(sanctions_matches)} match(es). "
                f"Highest similarity {top.similarity_score:.0f}% against '{top.matched_name}' on {top.list_type}."
            )
        if jurisdiction_risks:
            top_j = jurisdiction_risks[0]
            parts.append(f"Jurisdiction: {top_j.country} flagged ({top_j.list_type}).")
        if aml_flags:
            parts.append(f"AML: {len(aml_flags)} pattern flag(s) detected.")
        return " ".join(parts)

    # ── Data loading ──────────────────────────────────────────────────────────

    @staticmethod
    def _load_default_sanctions() -> list[dict[str, Any]]:
        path = settings.sample_data_dir / "sanctions_list.json"
        if path.exists():
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        logger.warning("Sanctions list not found, using empty list", path=str(path))
        return []
