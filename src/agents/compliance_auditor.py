"""Compliance Auditor Agent — sanctions, AML, and jurisdiction screening.

CrewAI skeleton with engine-backed tool. The engine provides deterministic
structured output; the LLM synthesises the evidence into natural language
for the Maestro Case evidence bundle.

crewai is optional: engine-mode (analyse()) works without it installed.
"""

from __future__ import annotations

from src.agents.base_agent import BaseOmniAgent, _build_llm
from src.core.logging_config import get_logger
from src.engines.compliance_engine import ComplianceEngine
from src.models.compliance import ComplianceResult
from src.models.payment import PaymentRecord

logger = get_logger("compliance_auditor_agent")

try:
    from crewai import Agent, Task
    from crewai.tools import BaseTool as _BaseTool
    _CREWAI = True
except ImportError:
    _CREWAI = False
    _BaseTool = object  # type: ignore[assignment,misc]


class ComplianceEngineTool(_BaseTool):  # type: ignore[misc]
    """Wraps ComplianceEngine as a crewai-compatible tool."""

    name: str = "compliance_engine"
    description: str = (
        "Screens a payment counterparty against sanctions lists, assesses jurisdiction risk, "
        "and detects AML patterns. Returns a structured compliance decision."
    )

    def __init__(self, engine: ComplianceEngine, **kwargs) -> None:
        if _CREWAI:
            super().__init__(**kwargs)
        self._engine = engine

    def _run(self, counterparty_name: str, counterparty_country: str,
             payment_amount: float = 0.0, source_currency: str = "USD") -> str:
        from decimal import Decimal
        from datetime import date
        from src.models.payment import CounterpartyDetails, PaymentPurpose, PaymentUrgency

        dummy = PaymentRecord(
            source_entity="AGENT_TOOL",
            source_account="AGENT_ACC",
            source_currency=source_currency,
            amount=Decimal(str(payment_amount)),
            target_currency=source_currency,
            counterparty=CounterpartyDetails(
                name=counterparty_name,
                account_number="UNKNOWN",
                bank_name="UNKNOWN",
                bank_swift_code="UNKNOWN",
                bank_country=counterparty_country,
            ),
            value_date=date.today(),
            purpose=PaymentPurpose.OTHER,
            reference="AGENT-TOOL-CALL",
        )
        return self._engine.run(dummy).model_dump_json(indent=2)


class ComplianceAuditorAgent(BaseOmniAgent):
    """CrewAI-backed compliance auditor with structured engine output."""

    agent_name = "ComplianceAuditorAgent"

    def __init__(self) -> None:
        super().__init__()
        self._engine = ComplianceEngine()
        self._crew_agent = None  # built lazily — requires crewai

    # ── Engine mode (no crewai required) ──────────────────────────────────────

    def analyse(self, payment: PaymentRecord) -> ComplianceResult:
        self._log_start(payment.payment_id)
        result = self._engine.run(payment)
        self._log_complete(payment.payment_id, result.decision.value)
        return result

    # ── CrewAI mode (requires crewai installed) ───────────────────────────────

    def build_task(self, payment: PaymentRecord) -> "Task":
        if not _CREWAI:
            raise RuntimeError("crewai is not installed. Run: pip install crewai")
        return Task(
            description=(
                f"Screen the following payment for compliance:\n"
                f"- Counterparty: {payment.counterparty.name}\n"
                f"- Country: {payment.counterparty.bank_country}\n"
                f"- Amount: {payment.amount} {payment.source_currency}\n"
                f"- Purpose: {payment.purpose.value}\n\n"
                "Use the compliance_engine tool to screen the counterparty. "
                "Summarise: sanctions matches, jurisdiction risk, AML flags, decision."
            ),
            expected_output=(
                "Compliance assessment: decision (CLEAR/FLAG/BLOCK), sanctions scores, "
                "jurisdiction risk, AML flags, regulatory references, recommended approver."
            ),
            agent=self.crew_agent,
        )

    @property
    def crew_agent(self) -> "Agent":
        if self._crew_agent is None:
            if not _CREWAI:
                raise RuntimeError("crewai is not installed. Run: pip install crewai")
            self._crew_agent = Agent(
                role="Chief Compliance Auditor",
                goal=(
                    "Screen every payment against global sanctions lists, AML regulations, "
                    "and FATF jurisdiction risk criteria. Produce a clear CLEAR/FLAG/BLOCK "
                    "decision with full evidence for every payment reviewed."
                ),
                backstory=(
                    "You are a senior compliance officer with 15 years of experience in "
                    "anti-money laundering, OFAC sanctions enforcement, and cross-border "
                    "payment regulation. Evidence-based and never block without cause."
                ),
                tools=[ComplianceEngineTool(engine=self._engine)],
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
            )
        return self._crew_agent
