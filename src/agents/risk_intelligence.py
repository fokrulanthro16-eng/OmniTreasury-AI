"""Risk Intelligence Agent — composite risk scoring across all dimensions.

crewai is optional: engine-mode (analyse()) works without it installed.
"""

from __future__ import annotations

from src.agents.base_agent import BaseOmniAgent
from src.core.logging_config import get_logger
from src.engines.risk_engine import RiskEngine
from src.models.payment import PaymentRecord
from src.models.risk import RiskResult

logger = get_logger("risk_intelligence_agent")

try:
    from crewai import Agent, Task
    from crewai.tools import BaseTool as _BaseTool
    _CREWAI = True
except ImportError:
    _CREWAI = False
    _BaseTool = object  # type: ignore[assignment,misc]


class RiskEngineTool(_BaseTool):  # type: ignore[misc]
    name: str = "risk_engine"
    description: str = (
        "Scores a payment across counterparty, concentration, market, and operational "
        "risk dimensions. Returns a composite risk score (0-100) with factor breakdown."
    )

    def __init__(self, engine: RiskEngine, **kwargs) -> None:
        if _CREWAI:
            super().__init__(**kwargs)
        self._engine = engine

    def _run(self, payment_id: str, counterparty_name: str, bank_country: str,
             bank_name: str, amount: float, source_currency: str,
             target_currency: str = "") -> str:
        from decimal import Decimal
        from datetime import date
        from src.models.payment import CounterpartyDetails, PaymentPurpose

        payment = PaymentRecord(
            payment_id=payment_id,
            source_entity="AGENT",
            source_account="AGENT",
            source_currency=source_currency,
            amount=Decimal(str(amount)),
            target_currency=target_currency or source_currency,
            counterparty=CounterpartyDetails(
                name=counterparty_name,
                account_number="UNKNOWN",
                bank_name=bank_name,
                bank_swift_code="UNKNOWN",
                bank_country=bank_country,
            ),
            value_date=date.today(),
            purpose=PaymentPurpose.OTHER,
            reference="AGENT-TOOL-CALL",
        )
        return self._engine.run(payment).model_dump_json(indent=2)


class RiskIntelligenceAgent(BaseOmniAgent):
    """CrewAI-backed risk intelligence agent with composite scoring engine."""

    agent_name = "RiskIntelligenceAgent"

    def __init__(self) -> None:
        super().__init__()
        self._engine = RiskEngine()
        self._crew_agent = None

    def analyse(self, payment: PaymentRecord) -> RiskResult:
        self._log_start(payment.payment_id)
        result = self._engine.run(payment)
        self._log_complete(payment.payment_id, f"score={result.composite_score}")
        return result

    def build_task(self, payment: PaymentRecord) -> "Task":
        if not _CREWAI:
            raise RuntimeError("crewai is not installed. Run: pip install crewai")
        return Task(
            description=(
                f"Assess risk for payment {payment.payment_id}:\n"
                f"- Counterparty: {payment.counterparty.name} ({payment.counterparty.bank_country})\n"
                f"- Bank: {payment.counterparty.bank_name}\n"
                f"- Amount: {payment.amount} {payment.source_currency} → {payment.target_currency}\n\n"
                "Score across all risk dimensions. Identify limit breaches and mitigations."
            ),
            expected_output=(
                "Risk score (0-100), risk level, factor breakdown, concentration checks, "
                "operational flags, mitigation recommendations."
            ),
            agent=self.crew_agent,
        )

    @property
    def crew_agent(self) -> "Agent":
        if self._crew_agent is None:
            if not _CREWAI:
                raise RuntimeError("crewai is not installed. Run: pip install crewai")
            self._crew_agent = Agent(
                role="Chief Risk Intelligence Officer",
                goal=(
                    "Produce an accurate, multi-dimensional risk score for every payment. "
                    "Surface limit breaches and operational flags before they become losses."
                ),
                backstory=(
                    "18 years in risk management at global transaction banks. Built the "
                    "counterparty risk framework that prevented $3B in losses during the 2020 "
                    "credit crisis."
                ),
                tools=[RiskEngineTool(engine=self._engine)],
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
            )
        return self._crew_agent
