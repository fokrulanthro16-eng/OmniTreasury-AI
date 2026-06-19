"""Risk intelligence engine: composite scoring across counterparty, concentration, market, and operational risk."""

from __future__ import annotations

import json
from typing import Any

from src.core.config import settings
from src.core.logging_config import get_logger
from src.models.payment import PaymentRecord
from src.models.risk import (
    ConcentrationCheck,
    OperationalFlag,
    RiskCategory,
    RiskFactor,
    RiskLevel,
    RiskResult,
)

logger = get_logger("risk_engine")

# Weights must sum to 1.0
_CATEGORY_WEIGHTS: dict[RiskCategory, float] = {
    RiskCategory.COUNTERPARTY: 0.30,
    RiskCategory.CONCENTRATION: 0.25,
    RiskCategory.MARKET: 0.25,
    RiskCategory.OPERATIONAL: 0.20,
}

# High-risk destination countries (non-FATF supplementary list)
_HIGH_RISK_COUNTRIES: frozenset[str] = frozenset({"RU", "BY", "VE", "CU", "SD", "SO"})

# Currencies with elevated FX volatility
_VOLATILE_CURRENCIES: frozenset[str] = frozenset({"TRY", "ARS", "NGN", "ZWL", "VES", "LBP"})


class RiskEngine:
    """Scores a payment across four risk dimensions and returns a weighted composite."""

    def __init__(self, thresholds_data: dict[str, Any] | None = None) -> None:
        self._thresholds = thresholds_data or self._load_default_thresholds()
        logger.info("RiskEngine initialised")

    # ── Public interface ──────────────────────────────────────────────────────

    def run(self, payment: PaymentRecord) -> RiskResult:
        """Produce a comprehensive risk result for the payment."""
        logger.info("Running risk assessment", payment_id=payment.payment_id)

        factors: list[RiskFactor] = [
            self._score_counterparty_risk(payment),
            self._score_concentration_risk(payment),
            self._score_market_risk(payment),
            self._score_operational_risk(payment),
        ]

        composite = self._compute_composite(factors)
        risk_level = self._classify_risk_level(composite)

        concentration_checks = self._run_concentration_checks(payment)
        operational_flags = self._detect_operational_flags(payment)

        limit_breaches = [
            c.dimension for c in concentration_checks if c.breached
        ]
        mitigations = self._build_mitigations(factors, risk_level, limit_breaches)

        result = RiskResult(
            payment_id=payment.payment_id,
            composite_score=composite,
            risk_level=risk_level,
            factors=factors,
            concentration_checks=concentration_checks,
            operational_flags=operational_flags,
            limit_breaches=limit_breaches,
            mitigation_recommendations=mitigations,
        )

        logger.info(
            "Risk assessment complete",
            payment_id=payment.payment_id,
            composite_score=composite,
            risk_level=risk_level.value,
            limit_breaches=limit_breaches,
        )
        return result

    # ── Risk factor scoring ───────────────────────────────────────────────────

    def _score_counterparty_risk(self, payment: PaymentRecord) -> RiskFactor:
        score = 20.0  # Base low risk
        desc_parts: list[str] = []

        country = payment.counterparty.bank_country.upper()[:2]
        if country in _HIGH_RISK_COUNTRIES:
            score += 50.0
            desc_parts.append(f"Bank country {country} is on high-risk country list (+50).")

        # No credit rating on file → moderate counterparty risk
        score += 15.0
        desc_parts.append("No external credit rating on file for counterparty bank (+15).")

        score = min(score, 100.0)
        return RiskFactor(
            category=RiskCategory.COUNTERPARTY,
            name="Counterparty Risk",
            score=score,
            weight=_CATEGORY_WEIGHTS[RiskCategory.COUNTERPARTY],
            description=" ".join(desc_parts) or "Standard counterparty assessment.",
            level=self._classify_risk_level(score),
        )

    def _score_concentration_risk(self, payment: PaymentRecord) -> RiskFactor:
        limits = self._thresholds.get("concentration_limits", {})
        country_limit = float(limits.get("single_country_usd", 5_000_000))
        amount_float = float(payment.amount)
        utilisation = (amount_float / country_limit) * 100 if country_limit else 0

        score = min(utilisation * 0.6, 100.0)
        desc = (
            f"This payment represents {utilisation:.1f}% of the single-country exposure limit "
            f"(${country_limit:,.0f})."
        )
        return RiskFactor(
            category=RiskCategory.CONCENTRATION,
            name="Concentration Risk",
            score=score,
            weight=_CATEGORY_WEIGHTS[RiskCategory.CONCENTRATION],
            description=desc,
            level=self._classify_risk_level(score),
        )

    def _score_market_risk(self, payment: PaymentRecord) -> RiskFactor:
        score = 15.0
        desc_parts: list[str] = []

        if payment.target_currency.upper() in _VOLATILE_CURRENCIES:
            score += 60.0
            desc_parts.append(f"{payment.target_currency} is classified as a volatile/restricted currency (+60).")

        if payment.source_currency != payment.target_currency:
            score += 10.0
            desc_parts.append("Cross-currency payment introduces FX settlement risk (+10).")

        score = min(score, 100.0)
        return RiskFactor(
            category=RiskCategory.MARKET,
            name="Market / FX Risk",
            score=score,
            weight=_CATEGORY_WEIGHTS[RiskCategory.MARKET],
            description=" ".join(desc_parts) or "Standard FX market conditions.",
            level=self._classify_risk_level(score),
        )

    def _score_operational_risk(self, payment: PaymentRecord) -> RiskFactor:
        score = 10.0
        desc_parts: list[str] = []

        if payment.submitted_by is None:
            score += 20.0
            desc_parts.append("Automated submission — no human initiator identified (+20).")

        if payment.invoice_reference is None:
            score += 15.0
            desc_parts.append("No invoice reference attached (+15).")

        score = min(score, 100.0)
        return RiskFactor(
            category=RiskCategory.OPERATIONAL,
            name="Operational Risk",
            score=score,
            weight=_CATEGORY_WEIGHTS[RiskCategory.OPERATIONAL],
            description=" ".join(desc_parts) or "Standard operational profile.",
            level=self._classify_risk_level(score),
        )

    # ── Concentration limit checks ────────────────────────────────────────────

    def _run_concentration_checks(self, payment: PaymentRecord) -> list[ConcentrationCheck]:
        limits = self._thresholds.get("concentration_limits", {})
        checks: list[ConcentrationCheck] = []
        amount = float(payment.amount)

        country_limit = float(limits.get("single_country_usd", 5_000_000))
        country_util = (amount / country_limit) * 100 if country_limit else 0
        checks.append(
            ConcentrationCheck(
                dimension=f"Country exposure: {payment.counterparty.bank_country}",
                current_exposure=amount,
                limit=country_limit,
                utilisation_pct=country_util,
                breached=country_util > 100,
            )
        )

        bank_limit = float(limits.get("single_bank_usd", 2_000_000))
        bank_util = (amount / bank_limit) * 100 if bank_limit else 0
        checks.append(
            ConcentrationCheck(
                dimension=f"Bank exposure: {payment.counterparty.bank_name}",
                current_exposure=amount,
                limit=bank_limit,
                utilisation_pct=bank_util,
                breached=bank_util > 100,
            )
        )

        return checks

    # ── Operational flags ─────────────────────────────────────────────────────

    def _detect_operational_flags(self, payment: PaymentRecord) -> list[OperationalFlag]:
        flags: list[OperationalFlag] = []
        amount = float(payment.amount)

        if amount >= float(settings.materiality_threshold):
            flags.append(
                OperationalFlag(
                    flag_type="MATERIALITY",
                    description=f"Payment exceeds materiality threshold of ${settings.materiality_threshold:,.0f}.",
                    severity=RiskLevel.HIGH,
                )
            )

        if payment.counterparty.is_internal is False and payment.purpose.value == "INTERCOMPANY_TRANSFER":
            flags.append(
                OperationalFlag(
                    flag_type="ENTITY_MISMATCH",
                    description="Purpose is INTERCOMPANY_TRANSFER but counterparty is not marked as internal.",
                    severity=RiskLevel.MEDIUM,
                )
            )

        return flags

    # ── Scoring helpers ───────────────────────────────────────────────────────

    def _compute_composite(self, factors: list[RiskFactor]) -> float:
        total = sum(f.score * f.weight for f in factors)
        return round(min(total, 100.0), 2)

    @staticmethod
    def _classify_risk_level(score: float) -> RiskLevel:
        if score >= 80:
            return RiskLevel.CRITICAL
        if score >= 60:
            return RiskLevel.HIGH
        if score >= 35:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def _build_mitigations(
        self,
        factors: list[RiskFactor],
        level: RiskLevel,
        breaches: list[str],
    ) -> list[str]:
        mitigations: list[str] = []
        if level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            mitigations.append("Obtain enhanced due diligence on counterparty before execution.")
        if any(f.category == RiskCategory.MARKET and f.score >= 60 for f in factors):
            mitigations.append("Consider forward contract to lock in exchange rate.")
        if breaches:
            mitigations.append(f"Concentration limit breached: {', '.join(breaches)}. Obtain Treasury Manager sign-off.")
        return mitigations

    # ── Data loading ──────────────────────────────────────────────────────────

    @staticmethod
    def _load_default_thresholds() -> dict[str, Any]:
        path = settings.sample_data_dir / "risk_thresholds.json"
        if path.exists():
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        logger.warning("Risk thresholds file not found, using defaults", path=str(path))
        return {"concentration_limits": {"single_country_usd": 5_000_000, "single_bank_usd": 2_000_000}}
