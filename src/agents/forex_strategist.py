"""Forex Strategist Agent — multi-provider rate comparison and route optimisation.

crewai is optional: engine-mode (analyse()) works without it installed.
"""

from __future__ import annotations

from src.agents.base_agent import BaseOmniAgent
from src.core.logging_config import get_logger
from src.engines.forex_engine import ForexEngine
from src.models.forex import FXResult
from src.models.payment import PaymentRecord

logger = get_logger("forex_strategist_agent")

try:
    from crewai import Agent, Task
    from crewai.tools import BaseTool as _BaseTool
    _CREWAI = True
except ImportError:
    _CREWAI = False
    _BaseTool = object  # type: ignore[assignment,misc]


class FXEngineTool(_BaseTool):  # type: ignore[misc]
    name: str = "fx_optimisation_engine"
    description: str = (
        "Fetches FX rates from multiple banking providers, ranks routes by total cost, "
        "and recommends the optimal execution timing and hedging strategy."
    )

    def __init__(self, engine: ForexEngine, **kwargs) -> None:
        if _CREWAI:
            super().__init__(**kwargs)
        self._engine = engine

    def _run(self, payment_json: str) -> str:
        import json
        from decimal import Decimal
        from datetime import date
        from src.models.payment import CounterpartyDetails, PaymentPurpose, PaymentUrgency

        data = json.loads(payment_json)
        payment = PaymentRecord(
            source_entity=data.get("source_entity", "AGENT"),
            source_account=data.get("source_account", "AGENT"),
            source_currency=data["source_currency"],
            amount=Decimal(str(data["amount"])),
            target_currency=data["target_currency"],
            counterparty=CounterpartyDetails(
                name=data.get("counterparty_name", "UNKNOWN"),
                account_number="UNKNOWN",
                bank_name="UNKNOWN",
                bank_swift_code="UNKNOWN",
                bank_country=data.get("counterparty_country", "XX"),
            ),
            value_date=date.today(),
            purpose=PaymentPurpose.OTHER,
            reference="AGENT-TOOL-CALL",
            urgency=PaymentUrgency(data.get("urgency", "T_PLUS_2")),
        )
        return self._engine.run(payment).model_dump_json(indent=2)


class ForexStrategistAgent(BaseOmniAgent):
    """CrewAI-backed FX strategist with rate optimisation engine."""

    agent_name = "ForexStrategistAgent"

    def __init__(self) -> None:
        super().__init__()
        self._engine = ForexEngine()
        self._crew_agent = None

    def analyse(self, payment: PaymentRecord) -> FXResult:
        self._log_start(payment.payment_id)
        result = self._engine.run(payment)
        self._log_complete(payment.payment_id, result.recommended_provider)
        return result

    def build_task(self, payment: PaymentRecord) -> "Task":
        if not _CREWAI:
            raise RuntimeError("crewai is not installed. Run: pip install crewai")
        return Task(
            description=(
                f"Analyse FX execution options for:\n"
                f"- Amount: {payment.amount} {payment.source_currency}\n"
                f"- Target Currency: {payment.target_currency}\n"
                f"- Urgency: {payment.urgency.value}\n\n"
                "Report: best provider, rate, savings vs benchmark, timing, hedge opportunity."
            ),
            expected_output=(
                "FX strategy: provider ranking, savings USD, timing recommendation, "
                "volatility flag, hedge opportunity."
            ),
            agent=self.crew_agent,
        )

    @property
    def crew_agent(self) -> "Agent":
        if self._crew_agent is None:
            if not _CREWAI:
                raise RuntimeError("crewai is not installed. Run: pip install crewai")
            self._crew_agent = Agent(
                role="Senior FX Strategist",
                goal=(
                    "Identify the most cost-effective FX execution route for every cross-border "
                    "payment. Quantify savings vs benchmark and recommend optimal timing."
                ),
                backstory=(
                    "FX specialist with 12 years on treasury desks of multinational corporations. "
                    "Expert in bid-ask spreads, forward curves, and interbank relationships."
                ),
                tools=[FXEngineTool(engine=self._engine)],
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
            )
        return self._crew_agent
