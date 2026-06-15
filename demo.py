#!/usr/bin/env python3
"""OmniTreasury AI — Hackathon Demo Mode.

Runs a full, judge-ready presentation through all treasury scenarios and
dashboard screens. Designed for a 5-minute live demo slot.

Usage:
  python demo.py full              # Complete 5-minute demo (all screens)
  python demo.py full --speed fast # Fast mode (minimal pauses, for testing)
  python demo.py full --export     # Export HTML screenshots to demo_output/
  python demo.py scenarios         # Live processing of 3 key scenarios only
  python demo.py cfo               # CFO Command Center only
  python demo.py liquidity         # Global Liquidity Overview only
  python demo.py risk              # Risk Heatmap only
  python demo.py fx                # FX Savings Report only
  python demo.py maestro           # Maestro Case Dashboard only
  python demo.py audit             # Audit Timeline only
  python demo.py summary           # Executive Summary only
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Ensure UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import click
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

from src.core.logging_config import configure_logging

configure_logging("WARNING")

console = Console(legacy_windows=False)

_SPEEDS = {"instant": 0, "fast": 0.5, "slow": 3.0}


def _pause(speed: str, seconds: float | None = None) -> None:
    delay = seconds if seconds is not None else _SPEEDS.get(speed, 1.5)
    if delay > 0:
        time.sleep(delay)


def _section_break(title: str, speed: str) -> None:
    console.print()
    console.print(Rule(f"[dim]{title}[/]", style="dim"))
    _pause(speed, _SPEEDS.get(speed, 1.5))


def _splash() -> None:
    logo = Text(justify="center")
    logo.append("\n")
    logo.append(
        "  ██████╗ ███╗   ███╗███╗   ██╗██╗\n"
        "  ██╔═══██╗████╗ ████║████╗  ██║██║\n"
        "  ██║   ██║██╔████╔██║██╔██╗ ██║██║\n"
        "  ██║   ██║██║╚██╔╝██║██║╚██╗██║██║\n"
        "  ╚██████╔╝██║ ╚═╝ ██║██║ ╚████║██║\n"
        "   ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝\n",
        style="bold cyan",
    )
    logo.append(
        "  TREASURY AI — Autonomous Treasury Control Tower\n",
        style="bold white",
    )
    logo.append(
        "  Powered by UiPath Maestro + CrewAI Multi-Agent Framework\n",
        style="dim",
    )
    logo.append(
        "  UiPath AgentHack 2026 — Maestro Case Track\n",
        style="dim yellow",
    )
    console.print(Panel(logo, border_style="cyan", expand=False))


def _run_demo_scenarios(speed: str) -> None:
    """Live-process 3 key scenarios with agent output visible."""
    from src.agents.decision_orchestrator import DecisionOrchestratorAgent
    from src.integrations.mock_banking_api import MockBankingAPIClient
    from src.integrations.mock_erp import MockERPClient
    from src.integrations.uipath_maestro import MaestroClient
    from src.models.decision import DecisionType
    from src.utils.audit_trail import audit_trail
    from src.utils.helpers import print_payment_header, print_decision_result, print_agent_summary_table

    configure_logging("INFO")

    erp = MockERPClient()
    orchestrator = DecisionOrchestratorAgent()
    banking = MockBankingAPIClient()
    maestro = MaestroClient()

    scenarios = [
        ("CLEAN_PAYMENT", "Scenario 1 — Clean Payment: Auto-Execute"),
        ("SANCTIONS_FLAG", "Scenario 2 — Sanctions Match: Maestro Escalation"),
        ("COMPLIANCE_BLOCK", "Scenario 3 — FATF Blacklist: Hard Reject"),
    ]

    for scenario_tag, label in scenarios:
        payment = erp.get_payment_by_scenario(scenario_tag)
        if payment is None:
            continue

        console.print()
        console.print(Rule(f"[bold cyan] {label} [/]"))
        print_payment_header(payment)
        _pause(speed, 0.5)

        audit_trail.record_payment_received(payment)
        decision = orchestrator.analyse(payment)

        if decision.compliance_result:
            audit_trail.record_compliance(decision.compliance_result)
        if decision.fx_result:
            audit_trail.record_forex(decision.fx_result)
        if decision.liquidity_result:
            audit_trail.record_liquidity(decision.liquidity_result)
        if decision.risk_result:
            audit_trail.record_risk(decision.risk_result)
        audit_trail.record_decision(decision)

        import decimal
        print_agent_summary_table(
            compliance_decision=decision.compliance_result.decision.value if decision.compliance_result else "N/A",
            fx_savings=decision.fx_result.estimated_savings_usd if decision.fx_result else decimal.Decimal("0"),
            liquidity_status=decision.liquidity_result.status.value if decision.liquidity_result else "N/A",
            risk_score=decision.risk_result.composite_score if decision.risk_result else 0.0,
        )
        print_decision_result(decision)

        if decision.decision == DecisionType.AUTO_EXECUTE and decision.fx_result:
            conf = banking.submit_payment(
                payment,
                fx_provider=decision.execution_route or "JP Morgan Treasury",
                execution_rate=decision.fx_result.recommended_rate,
            )
            audit_trail.record_execution(payment.payment_id, conf)
            console.print(f"\n[bold green]✓ Executed — Bank Confirmation: {conf}[/]")

        elif decision.decision == DecisionType.ESCALATE and decision.case_payload:
            case_id = maestro.create_case(decision.case_payload)
            audit_trail.record_case_created(
                payment.payment_id, case_id, decision.case_payload.assigned_role.value
            )
            console.print(f"\n[bold yellow]⊞ Maestro Case Created: {case_id}[/]")
            console.print(f"[dim]  Assigned to: {decision.case_payload.assigned_role.value.replace('_', ' ')}[/]")
            console.print(f"[dim]  SLA: {decision.case_payload.sla_minutes} minutes[/]")

        elif decision.decision == DecisionType.HARD_REJECT:
            console.print(f"\n[bold red]✗ Payment BLOCKED — FATF Blacklist Jurisdiction[/]")

        _pause(speed)

    configure_logging("WARNING")


def _build_state() -> "DemoState":  # type: ignore[name-defined]
    import io
    import contextlib
    from src.utils.demo_generator import build_demo_state

    buf = io.StringIO()
    with console.status("[bold cyan]  Running full pipeline on all 10 sample payments...", spinner="dots"):
        with contextlib.redirect_stdout(buf):
            state = build_demo_state(verbose=False)
    payment_count = len(state.runs)
    console.print(f"[green]✓ Pipeline complete — {payment_count} payments processed[/]")
    return state


# ── CLI group ─────────────────────────────────────────────────────────────────

@click.group()
def cli() -> None:
    """OmniTreasury AI — Hackathon Demo CLI."""


@cli.command()
@click.option("--speed", default="slow", type=click.Choice(["instant", "fast", "slow"]), help="Presentation pace")
@click.option("--export", "do_export", is_flag=True, default=False, help="Export screens as HTML to demo_output/")
def full(speed: str, do_export: bool) -> None:
    """Run the complete 5-minute hackathon demo presentation."""
    if do_export:
        from scripts.generate_screenshots import export_all
        console.print("[yellow]Export mode: all screens will be saved to demo_output/[/]")
        export_all()
        return

    _splash()
    _pause(speed, 2.0)

    # ── Act 1: The Problem + Live Agent Processing ────────────────────────────
    _section_break("ACT 1 — LIVE AGENT PROCESSING", speed)
    _run_demo_scenarios(speed)

    # ── Act 2: CFO Command Center ─────────────────────────────────────────────
    _section_break("ACT 2 — CFO COMMAND CENTER", speed)
    state = _build_state()

    from src.dashboard.cfo_dashboard import print_cfo_dashboard
    print_cfo_dashboard(state, console)
    _pause(speed)

    # ── Act 3: Risk Heatmap ───────────────────────────────────────────────────
    _section_break("ACT 3 — RISK INTELLIGENCE HEATMAP", speed)
    from src.dashboard.risk_heatmap import print_risk_heatmap
    print_risk_heatmap(state, console)
    _pause(speed)

    # ── Act 4: Global Liquidity ───────────────────────────────────────────────
    _section_break("ACT 4 — GLOBAL LIQUIDITY OVERVIEW", speed)
    from src.dashboard.liquidity_overview import print_liquidity_overview
    print_liquidity_overview(state, console)
    _pause(speed)

    # ── Act 5: FX Savings ─────────────────────────────────────────────────────
    _section_break("ACT 5 — FX OPTIMISATION REPORT", speed)
    from src.dashboard.fx_report import print_fx_report
    print_fx_report(state, console)
    _pause(speed)

    # ── Act 6: Maestro Cases ──────────────────────────────────────────────────
    _section_break("ACT 6 — UIPATH MAESTRO CASES", speed)
    from src.dashboard.maestro_dashboard import print_maestro_dashboard
    print_maestro_dashboard(state, console)
    _pause(speed)

    # ── Act 7: Audit Timeline ─────────────────────────────────────────────────
    _section_break("ACT 7 — IMMUTABLE AUDIT TRAIL", speed)
    from src.dashboard.audit_timeline import print_audit_timeline
    print_audit_timeline(state, console)
    _pause(speed)

    # ── Act 8: Executive Summary ──────────────────────────────────────────────
    _section_break("ACT 8 — EXECUTIVE SUMMARY", speed)
    from src.dashboard.executive_summary import print_executive_summary
    print_executive_summary(state, console)

    console.print()
    console.print(Rule("[bold cyan] END OF DEMO — OmniTreasury AI [/]"))
    console.print()


@cli.command()
@click.option("--speed", default="slow", type=click.Choice(["instant", "fast", "slow"]))
def scenarios(speed: str) -> None:
    """Live-process 3 demo scenarios (no dashboards)."""
    configure_logging("INFO")
    _splash()
    _pause(speed, 1.0)
    _run_demo_scenarios(speed)


@cli.command()
def cfo() -> None:
    """CFO Command Center dashboard."""
    state = _build_state()
    from src.dashboard.cfo_dashboard import print_cfo_dashboard
    print_cfo_dashboard(state, console)


@cli.command()
def summary() -> None:
    """Executive Summary screen."""
    state = _build_state()
    from src.dashboard.executive_summary import print_executive_summary
    print_executive_summary(state, console)


@cli.command()
def liquidity() -> None:
    """Global Liquidity Overview."""
    state = _build_state()
    from src.dashboard.liquidity_overview import print_liquidity_overview
    print_liquidity_overview(state, console)


@cli.command()
def risk() -> None:
    """Risk Intelligence Heatmap."""
    state = _build_state()
    from src.dashboard.risk_heatmap import print_risk_heatmap
    print_risk_heatmap(state, console)


@cli.command()
def fx() -> None:
    """FX Optimisation Report."""
    state = _build_state()
    from src.dashboard.fx_report import print_fx_report
    print_fx_report(state, console)


@cli.command()
def maestro() -> None:
    """Maestro Case Dashboard."""
    state = _build_state()
    from src.dashboard.maestro_dashboard import print_maestro_dashboard
    print_maestro_dashboard(state, console)


@cli.command()
def audit() -> None:
    """Audit Timeline View."""
    state = _build_state()
    from src.dashboard.audit_timeline import print_audit_timeline
    print_audit_timeline(state, console)


# ── Entrypoint ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cli()
