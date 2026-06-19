"""Maestro Case Dashboard — active cases, SLA status, and escalation summary."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich import box

if TYPE_CHECKING:
    from src.utils.demo_generator import DemoState

_SHARED = Console(legacy_windows=False)

_SLA_BY_LEVEL = {
    "COMPLIANCE_OFFICER": 240,
    "TREASURY_MANAGER": 120,
    "CFO": 480,
    "LEGAL": 1440,
}

_ESCALATION_COLOURS = {
    "COMPLIANCE_OFFICER": "yellow",
    "TREASURY_MANAGER": "cyan",
    "CFO": "red",
    "LEGAL": "magenta",
}


def _sla_remaining(created_at: datetime, sla_minutes: int) -> str:
    deadline = created_at + timedelta(minutes=sla_minutes)
    remaining = deadline - datetime.utcnow()
    total_secs = int(remaining.total_seconds())
    if total_secs <= 0:
        return "[bold red]OVERDUE[/]"
    hours, remainder = divmod(total_secs, 3600)
    minutes, _ = divmod(remainder, 60)
    if total_secs < 3600:
        return f"[bold yellow]{minutes}m[/]"
    return f"[{'green' if hours > 4 else 'yellow'}]{hours}h {minutes:02d}m[/]"


def _priority_badge(escalation_level: str) -> str:
    return {
        "CFO": "[bold white on red] P1 [/]",
        "LEGAL": "[bold white on red] P1 [/]",
        "COMPLIANCE_OFFICER": "[bold white on dark_orange] P2 [/]",
        "TREASURY_MANAGER": "[bold black on yellow] P3 [/]",
    }.get(escalation_level, "[dim] P4 [/]")


def print_maestro_dashboard(state: "DemoState", console: Console | None = None) -> None:
    c = console or _SHARED

    from src.models.decision import DecisionType

    c.print()
    c.print(Rule("[bold magenta] UIPATH MAESTRO CASE MANAGEMENT [/]"))
    c.print()

    escalated_runs = [r for r in state.runs if r.decision.decision == DecisionType.ESCALATE]

    if not escalated_runs:
        c.print("[dim]No active Maestro Cases in this run.[/]")
        return

    # ── Active cases table ─────────────────────────────────────────────────────
    cases_table = Table(
        title=f"Active Maestro Cases ({len(escalated_runs)} open)",
        box=box.ROUNDED,
        show_header=True,
    )
    cases_table.add_column("Case ID", style="bold magenta", min_width=11, no_wrap=True)
    cases_table.add_column("Payment ID", style="cyan", min_width=14, no_wrap=True)
    cases_table.add_column("Case Type", min_width=12)
    cases_table.add_column("Pri", justify="center")
    cases_table.add_column("Assigned To", style="bold", min_width=18)
    cases_table.add_column("SLA", justify="center", min_width=8)
    cases_table.add_column("Trigger", style="dim", min_width=12)
    cases_table.add_column("Comp", justify="center")
    cases_table.add_column("Risk", justify="right")

    for i, run in enumerate(escalated_runs, start=1):
        d = run.decision
        cp = d.case_payload
        if cp is None:
            continue

        esc_level = d.escalation_level.value if d.escalation_level else "UNKNOWN"
        esc_colour = _ESCALATION_COLOURS.get(esc_level, "white")
        risk_score = run.risk.composite_score if run.risk else 0.0
        comp_decision = run.compliance.decision.value if run.compliance else "N/A"
        comp_style = "green" if comp_decision == "CLEAR" else ("yellow" if comp_decision == "FLAG" else "red")

        # Simulate case creation timestamp offset per case
        created_offset = timedelta(minutes=i * 23 + 7)
        fake_created = datetime.utcnow() - created_offset
        sla_mins = _SLA_BY_LEVEL.get(esc_level, 240)

        trigger_text = d.rationales[0].trigger if d.rationales else "MANUAL"

        cases_table.add_row(
            f"CASE-{2040 + i:04d}",
            run.payment.payment_id,
            cp.case_type[:12],
            _priority_badge(esc_level),
            f"[{esc_colour}]{esc_level.replace('_', ' ')}[/]",
            _sla_remaining(fake_created, sla_mins),
            trigger_text[:12],
            f"[{comp_style}]{comp_decision}[/]",
            f"{risk_score:.1f}",
        )

    c.print(cases_table)

    # ── Evidence bundle preview ────────────────────────────────────────────────
    c.print()
    if escalated_runs:
        sample_run = escalated_runs[0]
        cp = sample_run.decision.case_payload
        if cp:
            evidence_items: list[str] = []
            if cp.compliance_report:
                comp_dec = cp.compliance_report.get("decision", "N/A")
                sanctions = cp.compliance_report.get("sanctions_matches", [])
                evidence_items.append(f"Compliance Report — Decision: {comp_dec}, Sanctions hits: {len(sanctions)}")
            if cp.risk_report:
                score = cp.risk_report.get("composite_score", 0)
                evidence_items.append(f"Risk Assessment — Composite Score: {score:.1f}/100")
            if cp.fx_analysis:
                prov = cp.fx_analysis.get("recommended_provider", "N/A")
                savings = cp.fx_analysis.get("estimated_savings_usd", 0)
                evidence_items.append(f"FX Analysis — Provider: {prov}, Savings: ${float(savings):,.2f}")
            if cp.liquidity_status:
                status = cp.liquidity_status.get("status", "N/A")
                evidence_items.append(f"Liquidity Status — {status}")
            if cp.agent_recommendations:
                for rec in cp.agent_recommendations[:2]:
                    evidence_items.append(f"AI Recommendation: {rec}")

            bundle_table = Table.grid(padding=(0, 2))
            bundle_table.add_column(style="bold yellow", no_wrap=True)
            bundle_table.add_column()
            for item in evidence_items:
                bundle_table.add_row("•", item)

            c.print(Panel(
                bundle_table,
                title=f"[bold]Evidence Bundle — CASE-{2041:04d} / {sample_run.payment.payment_id}[/]",
                subtitle="[dim]AI-generated · Attached to Maestro Case · Available for reviewer[/]",
                border_style="magenta",
            ))

    # ── Escalation breakdown ───────────────────────────────────────────────────
    c.print()
    from collections import Counter
    esc_by_level = Counter(
        r.decision.escalation_level.value
        for r in escalated_runs
        if r.decision.escalation_level
    )
    breakdown = Table(title="Escalation Breakdown", box=box.SIMPLE, show_header=True)
    breakdown.add_column("Assigned To", style="bold")
    breakdown.add_column("Cases Open", justify="center")
    breakdown.add_column("Avg SLA (min)", justify="right")
    breakdown.add_column("Urgency")
    for level, count in sorted(esc_by_level.items(), key=lambda x: -x[1]):
        colour = _ESCALATION_COLOURS.get(level, "white")
        sla = _SLA_BY_LEVEL.get(level, 240)
        urgency = "CRITICAL" if sla <= 120 else ("HIGH" if sla <= 480 else "STANDARD")
        urg_colour = "red" if urgency == "CRITICAL" else ("yellow" if urgency == "HIGH" else "green")
        breakdown.add_row(
            f"[{colour}]{level.replace('_', ' ')}[/]",
            str(count),
            str(sla),
            f"[{urg_colour}]{urgency}[/]",
        )
    c.print(breakdown)
    c.print()
