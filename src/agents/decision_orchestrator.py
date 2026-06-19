"""Decision Orchestrator Agent — synthesises all agent outputs into a single decision.

This agent coordinates the full treasury pipeline, either running engines
directly (fast mode) or dispatching a full CrewAI Crew (agentic mode).

crewai is optional: analyse() / engine mode works without it installed.
"""

from __future__ import annotations

from src.agents.base_agent import BaseOmniAgent
from src.agents.compliance_auditor import ComplianceAuditorAgent
from src.agents.forex_strategist import ForexStrategistAgent
from src.agents.liquidity_balancer import LiquidityBalancerAgent
from src.agents.risk_intelligence import RiskIntelligenceAgent
from src.core.logging_config import get_logger
from src.engines.decision_engine import DecisionEngine
from src.models.compliance import ComplianceResult
from src.models.decision import DecisionResult
from src.models.forex import FXResult
from src.models.liquidity import LiquidityResult
from src.models.payment import PaymentRecord
from src.models.risk import RiskResult

logger = get_logger("decision_orchestrator_agent")

try:
    from crewai import Agent, Crew, Process, Task
    _CREWAI = True
except ImportError:
    _CREWAI = False


class DecisionOrchestratorAgent(BaseOmniAgent):
    """Coordinates the full 4-agent parallel analysis and applies the decision matrix."""

    agent_name = "DecisionOrchestratorAgent"

    def __init__(self) -> None:
        super().__init__()
        self._compliance_agent = ComplianceAuditorAgent()
        self._forex_agent = ForexStrategistAgent()
        self._liquidity_agent = LiquidityBalancerAgent()
        self._risk_agent = RiskIntelligenceAgent()
        self._decision_engine = DecisionEngine()
        self._crew_agent = None

    # ── Engine mode (no crewai required) ──────────────────────────────────────

    def analyse(self, payment: PaymentRecord) -> DecisionResult:
        """Run all agents via their underlying engines and apply decision matrix."""
        self._log_start(payment.payment_id)
        logger.info("Running parallel agent analysis (engine mode)", payment_id=payment.payment_id)

        compliance: ComplianceResult = self._compliance_agent.analyse(payment)
        fx: FXResult = self._forex_agent.analyse(payment)
        liquidity: LiquidityResult = self._liquidity_agent.analyse(payment)
        risk: RiskResult = self._risk_agent.analyse(payment)

        decision: DecisionResult = self._decision_engine.run(
            payment, compliance, fx, liquidity, risk
        )
        self._log_complete(payment.payment_id, decision.decision.value)
        return decision

    # ── CrewAI agentic mode (requires crewai + API key) ───────────────────────

    def run_crew(self, payment: PaymentRecord) -> str:
        """Run the full CrewAI Crew with LLM reasoning on top of engine outputs."""
        if not _CREWAI:
            raise RuntimeError("crewai is not installed. Run: pip install crewai")

        logger.info("Running CrewAI crew (agentic mode)", payment_id=payment.payment_id)

        tasks = [
            self._compliance_agent.build_task(payment),
            self._forex_agent.build_task(payment),
            self._liquidity_agent.build_task(payment),
            self._risk_agent.build_task(payment),
            self._build_synthesis_task(payment),
        ]
        agents = [
            self._compliance_agent.crew_agent,
            self._forex_agent.crew_agent,
            self._liquidity_agent.crew_agent,
            self._risk_agent.crew_agent,
            self.crew_agent,
        ]
        crew = Crew(agents=agents, tasks=tasks, process=Process.sequential, verbose=True)
        return str(crew.kickoff())

    def _build_synthesis_task(self, payment: PaymentRecord) -> "Task":
        return Task(
            description=(
                f"Based on all specialist agent reports for payment {payment.payment_id}, "
                f"produce a final treasury decision:\n"
                f"- Amount: {payment.amount} {payment.source_currency} → {payment.target_currency}\n"
                f"- Counterparty: {payment.counterparty.name}\n\n"
                "Apply the decision matrix:\n"
                "  • Compliance BLOCK → HARD_REJECT\n"
                "  • Compliance FLAG → ESCALATE (Compliance Officer)\n"
                "  • Liquidity INSUFFICIENT → ESCALATE (Treasury Manager)\n"
                "  • Risk score ≥ 60 → ESCALATE (Treasury Manager)\n"
                "  • Amount ≥ $1M → ESCALATE (CFO)\n"
                "  • All clear → AUTO_EXECUTE"
            ),
            expected_output=(
                "Final decision: decision type, escalation level, trigger rationale, "
                "execution route (if auto-approving), case summary (if escalating)."
            ),
            agent=self.crew_agent,
        )

    @property
    def crew_agent(self) -> "Agent":
        if self._crew_agent is None:
            if not _CREWAI:
                raise RuntimeError("crewai is not installed. Run: pip install crewai")
            self._crew_agent = Agent(
                role="Head of Treasury Operations",
                goal=(
                    "Synthesise compliance, FX, liquidity, and risk analysis into a single "
                    "defensible decision. Route payments to execution or human review "
                    "with full evidence bundles."
                ),
                backstory=(
                    "Head of Treasury Operations for a global corporation. Accountable for "
                    "both operational efficiency and risk across all cross-border payments."
                ),
                llm=self.llm,
                verbose=True,
                allow_delegation=True,
            )
        return self._crew_agent
