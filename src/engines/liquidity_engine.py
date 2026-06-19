"""Liquidity engine: cash position validation, covenant checks, and netting discovery."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from src.core.config import settings
from src.core.exceptions import LiquidityError
from src.core.logging_config import get_logger
from src.models.liquidity import (
    CashPosition,
    FundingOption,
    LiquidityResult,
    LiquidityStatus,
    NettingOpportunity,
)
from src.models.payment import PaymentRecord

logger = get_logger("liquidity_engine")

_CENTS = Decimal("0.01")


class LiquidityEngine:
    """Validates cash availability and identifies intercompany netting to reduce FX costs."""

    def __init__(self, positions_data: dict[str, Any] | None = None) -> None:
        self._data = positions_data or self._load_default_positions()
        logger.info("LiquidityEngine initialised", entities=len(self._data.get("positions", {})))

    # ── Public interface ──────────────────────────────────────────────────────

    def run(self, payment: PaymentRecord) -> LiquidityResult:
        """Evaluate liquidity for the given payment."""
        logger.info("Running liquidity check", payment_id=payment.payment_id)

        position = self._get_position(payment.source_entity, payment.source_currency)
        payment_amount = payment.amount

        post_payment = (position.available_balance - payment_amount).quantize(_CENTS)
        post_headroom = (post_payment - position.covenant_minimum).quantize(_CENTS)

        covenant_at_risk = post_payment < position.covenant_minimum

        # Determine base status
        if post_payment < Decimal("0"):
            status = LiquidityStatus.INSUFFICIENT
        elif covenant_at_risk:
            status = LiquidityStatus.CONSTRAINED
        else:
            status = LiquidityStatus.SUFFICIENT

        # Scan for netting opportunity
        netting = self._find_netting_opportunity(payment)
        if netting and status != LiquidityStatus.INSUFFICIENT:
            status = LiquidityStatus.NETTING_AVAILABLE

        # Find funding sources if constrained or insufficient
        funding_options: list[FundingOption] = []
        if status in (LiquidityStatus.CONSTRAINED, LiquidityStatus.INSUFFICIENT):
            funding_options = self._find_funding_options(payment)

        recommended_action = self._recommend_action(status, netting, funding_options)

        result = LiquidityResult(
            payment_id=payment.payment_id,
            status=status,
            source_position=position,
            post_payment_balance=post_payment,
            post_payment_headroom=post_headroom,
            covenant_at_risk=covenant_at_risk,
            netting_opportunity=netting,
            funding_options=funding_options,
            recommended_action=recommended_action,
        )

        logger.info(
            "Liquidity check complete",
            payment_id=payment.payment_id,
            status=status.value,
            post_payment=str(post_payment),
            covenant_at_risk=covenant_at_risk,
        )
        return result

    # ── Position lookup ───────────────────────────────────────────────────────

    def _get_position(self, entity: str, currency: str) -> CashPosition:
        positions = self._data.get("positions", {})
        key = f"{entity}:{currency}"
        raw = positions.get(key) or positions.get(entity, {}).get(currency)

        if raw is None:
            logger.warning("No position found, defaulting to zero", entity=entity, currency=currency)
            return CashPosition(
                entity=entity,
                account_id="DEFAULT",
                currency=currency,
                available_balance=Decimal("0"),
                total_balance=Decimal("0"),
                covenant_minimum=Decimal("0"),
            )

        return CashPosition(
            entity=raw["entity"],
            account_id=raw["account_id"],
            currency=raw["currency"],
            available_balance=Decimal(str(raw["available_balance"])),
            total_balance=Decimal(str(raw["total_balance"])),
            covenant_minimum=Decimal(str(raw.get("covenant_minimum", "0"))),
        )

    # ── Netting discovery ─────────────────────────────────────────────────────

    def _find_netting_opportunity(self, payment: PaymentRecord) -> NettingOpportunity | None:
        """Check if an offsetting intercompany receivable exists."""
        netting_candidates = self._data.get("netting_candidates", [])
        for candidate in netting_candidates:
            if (
                candidate.get("counterparty", "").upper() == payment.counterparty.name.upper()
                and candidate.get("currency") == payment.target_currency
                and candidate.get("is_internal", False)
            ):
                offsetting_amount = Decimal(str(candidate["amount"]))
                net_exposure = abs(payment.amount - offsetting_amount)
                fx_saving = (min(payment.amount, offsetting_amount) * Decimal("0.005")).quantize(_CENTS)
                return NettingOpportunity(
                    offsetting_payment_id=candidate["payment_id"],
                    counterparty=candidate["counterparty"],
                    currency=candidate["currency"],
                    offsetting_amount=offsetting_amount,
                    net_exposure=net_exposure,
                    estimated_fx_saving_usd=fx_saving,
                    description=(
                        f"Intercompany netting with {candidate['counterparty']}: "
                        f"net down to {float(net_exposure):,.2f} {candidate['currency']}. "
                        f"Estimated FX saving: ${float(fx_saving):,.2f}."
                    ),
                )
        return None

    # ── Funding options ───────────────────────────────────────────────────────

    def _find_funding_options(self, payment: PaymentRecord) -> list[FundingOption]:
        options: list[FundingOption] = []
        funding_sources = self._data.get("funding_sources", [])
        for src in funding_sources:
            if src.get("currency") == payment.source_currency:
                options.append(
                    FundingOption(
                        source_entity=src["entity"],
                        source_account=src["account_id"],
                        available_amount=Decimal(str(src["available"])),
                        currency=src["currency"],
                        funding_type=src.get("type", "INTERCOMPANY_LOAN"),
                        estimated_cost_usd=Decimal(str(src.get("cost_usd", "0"))),
                        description=src.get("description", ""),
                    )
                )
        return options

    # ── Recommendation ────────────────────────────────────────────────────────

    def _recommend_action(
        self,
        status: LiquidityStatus,
        netting: NettingOpportunity | None,
        funding_options: list[FundingOption],
    ) -> str:
        if status == LiquidityStatus.SUFFICIENT:
            return "Sufficient liquidity. Proceed to FX execution."
        if status == LiquidityStatus.NETTING_AVAILABLE:
            return f"Netting opportunity identified. Recommend netting with {netting.counterparty} to eliminate FX transaction."  # type: ignore[union-attr]
        if status == LiquidityStatus.CONSTRAINED:
            if funding_options:
                top = funding_options[0]
                return f"Covenant at risk post-payment. Recommend pre-funding from {top.source_entity} ({top.funding_type})."
            return "Covenant constraint detected. Escalate to Treasury Manager before execution."
        if status == LiquidityStatus.INSUFFICIENT:
            if funding_options:
                top = funding_options[0]
                return f"Insufficient funds. Fund from {top.source_entity} before executing payment."
            return "Insufficient funds and no internal funding available. Payment cannot proceed."
        return ""

    # ── Data loading ──────────────────────────────────────────────────────────

    @staticmethod
    def _load_default_positions() -> dict[str, Any]:
        path = settings.sample_data_dir / "liquidity_positions.json"
        if path.exists():
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        logger.warning("Liquidity positions file not found", path=str(path))
        return {"positions": {}, "netting_candidates": [], "funding_sources": []}
