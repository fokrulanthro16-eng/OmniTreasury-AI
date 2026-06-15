"""Abstract base for all OmniTreasury CrewAI agents.

Each agent wraps one or more business engines and exposes a CrewAI-compatible
interface. The engine does the deterministic work; the LLM adds reasoning,
evidence synthesis, and natural-language output.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.core.config import settings
from src.core.logging_config import get_logger
from src.models.payment import PaymentRecord

logger = get_logger("base_agent")


def _build_llm() -> Any:
    """Construct the LLM instance based on available API keys."""
    if settings.anthropic_api_key:
        try:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model="claude-sonnet-4-6",
                api_key=settings.anthropic_api_key,
                temperature=0.0,
            )
        except ImportError:
            logger.warning("langchain-anthropic not installed, falling back to OpenAI.")

    if settings.openai_api_key:
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model="gpt-4o",
                api_key=settings.openai_api_key,
                temperature=0.0,
            )
        except ImportError:
            logger.warning("langchain-openai not installed.")

    logger.warning("No LLM API key configured. Agents will run in engine-only mode.")
    return None


class BaseOmniAgent(ABC):
    """Shared interface all OmniTreasury agents must implement."""

    agent_name: str = "BaseAgent"

    def __init__(self) -> None:
        self.llm = _build_llm()
        self.logger = get_logger(self.agent_name)

    @abstractmethod
    def analyse(self, payment: PaymentRecord) -> Any:
        """Run analysis on the payment and return a typed result model."""
        ...

    def _log_start(self, payment_id: str) -> None:
        self.logger.info(f"{self.agent_name} starting analysis", payment_id=payment_id)

    def _log_complete(self, payment_id: str, decision: str) -> None:
        self.logger.info(
            f"{self.agent_name} analysis complete",
            payment_id=payment_id,
            decision=decision,
        )
