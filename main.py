#!/usr/bin/env python3
"""OmniTreasury AI — Autonomous Treasury Control Tower.

Entry point for:
  - Standalone Python CLI execution
  - UiPath Studio Python Script activity
  - CI/CD pipeline demo runs

Usage:
  python main.py process --scenario 1          # Demo: clean payment auto-approve
  python main.py process --scenario 2          # Demo: compliance escalation
  python main.py process --scenario 3          # Demo: liquidity crisis + netting
  python main.py process --payment-id PAY-2026-0001
  python main.py batch                         # Process all sample payments
  python main.py parse-swift <path_to_mt103>  # Parse a SWIFT MT103 file
  python main.py dashboard                    # Print live dashboard summary
"""

from __future__ import annotations

import sys

# Ensure UTF-8 output on Windows (PowerShell/cmd default to cp1252)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import json
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

# ── Ensure src/ is on the path when invoked from UiPath Studio ────────────────
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.core.config import settings
from src.core.logging_config import configure_logging, get_logger
from src.agents.decision_orchestrator import DecisionOrchestratorAgent
from src.agents.document_intelligence import DocumentIntelligenceAgent
from src.integrations.mock_erp import MockERPClient
from src.integrations.mock_banking_api import MockBankingAPIClient
from src.integrations.uipath_maestro import MaestroClient
from src.models.decision import DecisionType
from src.utils.audit_trail import audit_trail
from src.utils.helpers import (
    console,
    print_payment_header,
    print_decision_result,
    print_agent_summary_table,
)

logger = get_logger("main")

_SCENARIO_MAP = {
    1: "CLEAN_PAYMENT",
    2: "SANCTIONS_FLAG",
    3: "LIQUIDITY_CONSTRAINED",
    4: "CFO_APPROVAL",
    5: "NETTING_OPPORTUNITY",
    6: "COMPLIANCE_BLOCK",
}


# ── CLI definition ─────────────────────────────────────────────────────────────

@click.group()
@click.option("--log-level", default=settings.log_level, help="Logging level")
def cli(log_level: str) -> None:
    """OmniTreasury AI — Autonomous Treasury Control Tower."""
    configure_logging(log_level)


@cli.command()
@click.option("--payment-id", default=None, help="Process a specific payment by ID")
@click.option("--scenario", default=1, type=int, help="Demo scenario 1-6")
def process(payment_id: str | None, scenario: int) -> None:
    """Process a single payment through the full agent pipeline."""
    erp = MockERPClient()

    if payment_id:
        payment = erp.get_payment_by_id(payment_id)
        if payment is None:
            console.print(f"[red]Payment {payment_id} not found in ERP.[/]")
            sys.exit(1)
    else:
        scenario_tag = _SCENARIO_MAP.get(scenario, "CLEAN_PAYMENT")
        payment = erp.get_payment_by_scenario(scenario_tag)
        if payment is None:
            console.print(f"[red]Scenario '{scenario_tag}' not found in sample data.[/]")
            sys.exit(1)

    _run_pipeline(payment)


@cli.command()
def batch() -> None:
    """Process all sample payments through the pipeline."""
    erp = MockERPClient()
    payments = erp.get_pending_payments()

    console.print(Rule(f"[bold cyan]BATCH PROCESSING — {len(payments)} PAYMENTS[/]"))

    results = {"AUTO_EXECUTE": 0, "ESCALATE": 0, "HARD_REJECT": 0}
    for i, payment in enumerate(payments, start=1):
        console.print(f"\n[bold]── Payment {i}/{len(payments)}: {payment.payment_id} ──[/]")
        decision = _run_pipeline(payment, quiet=True)
        results[decision.decision.value] += 1

    console.print(Rule("[bold cyan]BATCH RESULTS[/]"))
    console.print(f"  [green]Auto-Executed : {results['AUTO_EXECUTE']}[/]")
    console.print(f"  [yellow]Escalated     : {results['ESCALATE']}[/]")
    console.print(f"  [red]Hard Rejected  : {results['HARD_REJECT']}[/]")
    console.print(f"  Total processed: {len(payments)}\n")

    export_path = _ROOT / "audit_trail_export.json"
    audit_trail.export_json(export_path)
    console.print(f"[dim]Audit trail exported → {export_path}[/]")


@cli.command("parse-swift")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--entity", default="CORP-HQ", help="Source entity name")
def parse_swift(file_path: str, entity: str) -> None:
    """Parse a SWIFT MT103 file and display extracted payment data."""
    configure_logging(settings.log_level)
    raw = Path(file_path).read_text(encoding="utf-8")
    agent = DocumentIntelligenceAgent()
    payment = agent.parse_swift(raw, source_entity=entity)
    console.print(Panel(
        payment.model_dump_json(indent=2),
        title="[bold cyan]Parsed MT103 → PaymentRecord[/]",
        border_style="cyan",
    ))


@cli.command()
def dashboard() -> None:
    """Display OmniTreasury AI audit trail dashboard."""
    records = audit_trail.get_all_records()
    if not records:
        console.print("[yellow]No audit records yet. Run 'process' or 'batch' first.[/]")
        return

    from collections import Counter
    from rich.table import Table

    event_counts = Counter(r.event_type.value for r in records)
    table = __import__("rich.table", fromlist=["Table"]).Table(title="Audit Event Summary")
    table.add_column("Event Type", style="cyan")
    table.add_column("Count", style="bold")
    for event, count in sorted(event_counts.items(), key=lambda x: -x[1]):
        table.add_row(event, str(count))
    console.print(table)


# ── Core pipeline function (also callable from UiPath Studio) ──────────────────

def run_payment_pipeline(payment_id: str) -> dict:
    """Process a payment by ID and return a JSON-serialisable result dict.

    This function is the primary UiPath Studio integration point:
      - Call via Python Script activity
      - Pass payment_id as argument
      - Read returned dict for Maestro Case creation

    Returns:
        dict with keys: payment_id, decision, escalation_level,
                        case_payload (if escalating), execution_route,
                        summary, audit_record_count
    """
    configure_logging(settings.log_level)
    erp = MockERPClient()
    payment = erp.get_payment_by_id(payment_id)
    if payment is None:
        return {"error": f"Payment {payment_id} not found", "payment_id": payment_id}

    decision = _run_pipeline(payment, quiet=True)

    return {
        "payment_id": decision.payment_id,
        "decision": decision.decision.value,
        "escalation_level": decision.escalation_level.value if decision.escalation_level else None,
        "execution_route": decision.execution_route,
        "summary": decision.summary,
        "case_payload": decision.case_payload.model_dump() if decision.case_payload else None,
        "audit_record_count": len(audit_trail.get_records_for_payment(payment_id)),
    }


def _run_pipeline(payment, quiet: bool = False):
    """Internal pipeline execution — used by both CLI and API modes."""
    audit_trail.record_payment_received(payment)

    if not quiet:
        console.print(Rule("[bold cyan]OMNITREASURY AI — PAYMENT ANALYSIS[/]"))
        print_payment_header(payment)

    orchestrator = DecisionOrchestratorAgent()
    decision = orchestrator.analyse(payment)

    # Record all agent outputs to audit trail
    if decision.compliance_result:
        audit_trail.record_compliance(decision.compliance_result)
    if decision.fx_result:
        audit_trail.record_forex(decision.fx_result)
    if decision.liquidity_result:
        audit_trail.record_liquidity(decision.liquidity_result)
    if decision.risk_result:
        audit_trail.record_risk(decision.risk_result)
    audit_trail.record_decision(decision)

    if not quiet:
        # Print agent summary table
        print_agent_summary_table(
            compliance_decision=decision.compliance_result.decision.value if decision.compliance_result else "N/A",
            fx_savings=decision.fx_result.estimated_savings_usd if decision.fx_result else __import__("decimal").Decimal("0"),
            liquidity_status=decision.liquidity_result.status.value if decision.liquidity_result else "N/A",
            risk_score=decision.risk_result.composite_score if decision.risk_result else 0.0,
        )
        print_decision_result(decision)

    # ── Auto-execute path ─────────────────────────────────────────────────────
    if decision.decision == DecisionType.AUTO_EXECUTE and decision.fx_result:
        banking = MockBankingAPIClient()
        confirmation_ref = banking.submit_payment(
            payment,
            fx_provider=decision.execution_route or "HSBC Global FX",
            execution_rate=decision.fx_result.recommended_rate,
        )
        audit_trail.record_execution(payment.payment_id, confirmation_ref)
        if not quiet:
            console.print(f"\n[green]✓ Payment executed. Bank confirmation: {confirmation_ref}[/]")

    # ── Escalation path — create Maestro Case ────────────────────────────────
    elif decision.decision == DecisionType.ESCALATE and decision.case_payload:
        maestro = MaestroClient()
        case_id = maestro.create_case(decision.case_payload)
        audit_trail.record_case_created(
            payment.payment_id,
            case_id,
            decision.case_payload.assigned_role.value,
        )
        if not quiet:
            console.print(f"\n[yellow]⚠ Maestro Case created: {case_id}[/]")

    # ── Hard reject path ──────────────────────────────────────────────────────
    elif decision.decision == DecisionType.HARD_REJECT:
        if not quiet:
            console.print(f"\n[red]✗ Payment {payment.payment_id} BLOCKED and rejected.[/]")

    if not quiet:
        console.print(Rule("[dim]Analysis complete[/]"))

    return decision


# ── UiPath Studio direct invocation ───────────────────────────────────────────

def uipath_process_payment(payment_id: str) -> str:
    """Callable from UiPath Studio Python Script activity.

    Returns JSON string for easy consumption in UiPath workflows.
    """
    result = run_payment_pipeline(payment_id)
    return json.dumps(result, indent=2, default=str)


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cli()
