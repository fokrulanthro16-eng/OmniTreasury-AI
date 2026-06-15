"""Document Intelligence Agent — parses SWIFT MT103 and financial documents.

crewai is optional: parse_swift() and analyse() work without it installed.
"""

from __future__ import annotations

from src.agents.base_agent import BaseOmniAgent
from src.core.logging_config import get_logger
from src.models.payment import PaymentRecord
from src.parsers.swift_mt103 import parse_mt103

logger = get_logger("document_intelligence_agent")

try:
    from crewai import Agent, Task
    from crewai.tools import BaseTool as _BaseTool
    _CREWAI = True
except ImportError:
    _CREWAI = False
    _BaseTool = object  # type: ignore[assignment,misc]


class SWIFTMT103Tool(_BaseTool):  # type: ignore[misc]
    name: str = "swift_mt103_parser"
    description: str = (
        "Parses a raw SWIFT MT103 Single Customer Credit Transfer message and extracts "
        "all payment fields: reference, value date, currency, amount, counterparty, "
        "and remittance information."
    )

    def __init__(self, **kwargs) -> None:
        if _CREWAI:
            super().__init__(**kwargs)

    def _run(self, raw_message: str, source_entity: str = "CORP-HQ") -> str:
        try:
            payment = parse_mt103(raw_message, source_entity=source_entity)
            return payment.model_dump_json(indent=2)
        except Exception as exc:
            return f"Parse error: {exc}"


class DocumentIntelligenceAgent(BaseOmniAgent):
    """Extracts structured payment data from raw SWIFT messages and documents."""

    agent_name = "DocumentIntelligenceAgent"

    def __init__(self) -> None:
        super().__init__()
        self._crew_agent = None

    def analyse(self, payment: PaymentRecord) -> PaymentRecord:
        """Enrich a payment record by parsing its attached SWIFT message (if any)."""
        if payment.swift_message:
            try:
                parsed = parse_mt103(payment.swift_message, source_entity=payment.source_entity)
                parsed_dict = parsed.model_dump()
                parsed_dict["payment_id"] = payment.payment_id
                return PaymentRecord(**parsed_dict)
            except Exception as exc:
                logger.warning(
                    "SWIFT parse failed, returning original payment",
                    payment_id=payment.payment_id,
                    error=str(exc),
                )
        return payment

    def parse_swift(self, raw_message: str, source_entity: str = "CORP-HQ") -> PaymentRecord:
        """Parse a SWIFT MT103 string directly into a PaymentRecord."""
        return parse_mt103(raw_message, source_entity=source_entity)

    def build_task(self, raw_message: str) -> "Task":
        if not _CREWAI:
            raise RuntimeError("crewai is not installed. Run: pip install crewai")
        return Task(
            description=(
                "Parse the following SWIFT MT103 message and extract all payment fields:\n\n"
                f"{raw_message}\n\n"
                "Use the swift_mt103_parser tool and return a complete payment data structure."
            ),
            expected_output=(
                "Extracted payment: reference, value date, currency, amount, "
                "ordering customer, beneficiary, bank BIC, remittance info, inferred purpose."
            ),
            agent=self.crew_agent,
        )

    @property
    def crew_agent(self) -> "Agent":
        if self._crew_agent is None:
            if not _CREWAI:
                raise RuntimeError("crewai is not installed. Run: pip install crewai")
            self._crew_agent = Agent(
                role="Document Intelligence Specialist",
                goal=(
                    "Extract clean, structured payment data from any financial document "
                    "so that no manual data entry is required."
                ),
                backstory=(
                    "Financial document specialist with deep expertise in SWIFT message standards, "
                    "ISO 20022, and bank statement formats."
                ),
                tools=[SWIFTMT103Tool()],
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
            )
        return self._crew_agent
