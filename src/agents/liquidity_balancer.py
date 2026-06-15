"""Liquidity Balancer Agent — cash position validation and netting discovery.

crewai is optional: engine-mode (analyse()) works without it installed.
"""

from __future__ import annotations

from src.agents.base_agent import BaseOmniAgent
from src.core.logging_config import get_logger
from src.engines.liquidity_engine import LiquidityEngine
from src.models.liquidity import LiquidityResult
from src.models.payment import PaymentRecord

logger = get_logger("liquidity_balancer_agent")

try:
    from crewai import Agent, Task
    from crewai.tools import BaseTool as _BaseTool
    _CREWAI = True
except ImportError:
    _CREWAI = False
    _BaseTool = object  # type: ignore[assignment,misc]


class LiquidityEngineTool(_BaseTool):  # type: ignore[misc]
    name: str = "liquidity_engine"
    description: str = (
        "Checks available cash positions for the source entity and currency. "
        "Identifies covenant breaches, netting opportunities, and alternative funding sources."
    )

    def __init__(self, engine: LiquidityEngine, **kwargs) -> None:
        if _CREWAI:
            super().__init__(**kwargs)
        self._engine = engine

    def _run(self, payment_id: str, source_entity: str, source_currency: str,
             amount: float, counterparty_name: str = "", target_currency: str = "") -> str:
        from decimal import Decimal
        from datetime import date
        from src.models.payment import CounterpartyDetails, PaymentPurpose

        payment = PaymentRecord(
            payment_id=payment_id,
            source_entity=source_entity,
            source_account="AGENT",
            source_currency=source_currency,
            amount=Decimal(str(amount)),
            target_currency=target_currency or source_currency,
            counterparty=CounterpartyDetails(
                name=counterparty_name or "UNKNOWN",
                account_number="UNKNOWN",
                bank_name="UNKNOWN",
                bank_swift_code="UNKNOWN",
                bank_country="XX",
            ),
            value_date=date.today(),
            purpose=PaymentPurpose.OTHER,
            reference="AGENT-TOOL-CALL",
        )
        return self._engine.run(payment).model_dump_json(indent=2)


class LiquidityBalancerAgent(BaseOmniAgent):
    """CrewAI-backed liquidity balancer with cash position engine."""

    agent_name = "LiquidityBalancerAgent"

    def __init__(self) -> None:
        super().__init__()
        self._engine = LiquidityEngine()
        self._crew_agent = None

    def analyse(self, payment: PaymentRecord) -> LiquidityResult:
        self._log_start(payment.payment_id)
        result = self._engine.run(payment)
        self._log_complete(payment.payment_id, result.status.value)
        return result

    def build_task(self, payment: PaymentRecord) -> "Task":
        if not _CREWAI:
            raise RuntimeError("crewai is not installed. Run: pip install crewai")
        return Task(
            description=(
                f"Validate liquidity for payment {payment.payment_id}:\n"
                f"- Source: {payment.source_entity} ({payment.source_currency})\n"
                f"- Amount: {payment.amount}\n"
                f"- Counterparty: {payment.counterparty.name}\n\n"
                "Report: available balance, post-payment position, covenant status, "
                "netting opportunity, recommended action."
            ),
            expected_output=(
                "Liquidity status (SUFFICIENT/CONSTRAINED/INSUFFICIENT/NETTING_AVAILABLE), "
                "cash positions, covenant compliance, netting details, funding options."
            ),
            agent=self.crew_agent,
        )

    @property
    def crew_agent(self) -> "Agent":
        if self._crew_agent is None:
            if not _CREWAI:
                raise RuntimeError("crewai is not installed. Run: pip install crewai")
            self._crew_agent = Agent(
                role="Corporate Treasury Liquidity Manager",
                goal=(
                    "Ensure every payment has sufficient funding without breaching liquidity "
                    "covenants. Proactively identify intercompany netting to eliminate "
                    "unnecessary FX transactions."
                ),
                backstory=(
                    "Manages global liquidity for a Fortune 500 corporation across 28 countries. "
                    "Expert in covenant frameworks and intercompany netting strategies."
                ),
                tools=[LiquidityEngineTool(engine=self._engine)],
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
            )
        return self._crew_agent
