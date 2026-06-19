"""Mock FX data feed — simulates Bloomberg/Reuters spot and forward rate delivery."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from src.core.config import settings
from src.core.logging_config import get_logger

logger = get_logger("mock_fx_feed")


class MockFXFeedClient:
    """Provides simulated FX market data for demo and testing purposes."""

    def __init__(self) -> None:
        self._data = self._load_rates()
        logger.info("MockFXFeedClient ready", pairs=list(self._data.get("rates", {}).keys()))

    def get_spot_rate(self, base: str, quote: str) -> Decimal:
        pair = f"{base.upper()}/{quote.upper()}"
        rates = self._data.get("rates", {})
        rate = rates.get(pair)
        if rate is not None:
            return Decimal(str(rate))
        inv_pair = f"{quote.upper()}/{base.upper()}"
        inv_rate = rates.get(inv_pair)
        if inv_rate is not None:
            return (Decimal("1") / Decimal(str(inv_rate))).quantize(Decimal("0.0001"))
        logger.warning("No rate found for pair, returning 1.0", pair=pair)
        return Decimal("1.0")

    def get_volatility(self, base: str, quote: str) -> float:
        pair = f"{base.upper()}/{quote.upper()}"
        return float(self._data.get("volatility", {}).get(pair, 0.05))

    def get_trend(self, base: str, quote: str) -> str:
        pair = f"{base.upper()}/{quote.upper()}"
        return str(self._data.get("trends", {}).get(pair, "STABLE"))

    def _load_rates(self) -> dict[str, Any]:
        path = settings.sample_data_dir / "fx_rates.json"
        if path.exists():
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        logger.warning("FX rates file not found", path=str(path))
        return {"rates": {}, "volatility": {}, "trends": {}}
