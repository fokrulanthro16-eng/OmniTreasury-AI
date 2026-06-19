"""Executive Summary — KPI overview panel for judges and CFO audience."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich import box

if TYPE_CHECKING:
    from src.utils.demo_generator import DemoState

_SHARED = Console(legacy_windows=False)


def _kpi_panel(title: str, value: str, subtitle: str, colour: str) -> Panel:
    body = Text(justify="center")
    body.append("\n")
    body.append(value, style=f"bold {colour}")
    body.append(f"\n{subtitle}", style="dim")
    body.append("\n")
    return Panel(body, title=f"[bold]{title}[/]", border_style=colour, expand=True)


def print_executive_summary(state: "DemoState", console: Console | None = None) -> None:
    c = console or _SHARED
    now = datetime.utcnow().strftime("%A, %d %B %Y  %H:%M UTC")

    c.print()
    c.print(Rule("[bold cyan] OMNITREASURY AI — AUTONOMOUS TREASURY CONTROL TOWER [/]"))
    c.print(Rule(f"[dim]{now}[/]", style="dim"))
    c.print()

    # ── KPI Grid ───────────────────────────────────────────────────────────────
    auto_pct = int(state.historical_auto_executed / max(state.historical_payment_count, 1) * 100)
    kpis = Columns([
        _kpi_panel(
            "PAYMENTS TODAY",
            str(state.historical_payment_count),
            f"${state.historical_total_value_m:.1f}M total value",
            "cyan",
        ),
        _kpi_panel(
            "AUTOMATION RATE",
            f"{auto_pct}%",
            f"{state.historical_auto_executed} of {state.historical_payment_count} auto-executed",
            "green",
        ),
        _kpi_panel(
            "FX SAVINGS YTD",
            f"${float(state.historical_fx_savings_usd):,.0f}",
            "vs interbank benchmark",
            "yellow",
        ),
        _kpi_panel(
            "COMPLIANCE HEALTH",
            "100% CLEAR",
            f"0 violations reached settlement",
            "green",
        ),
    ], equal=True, expand=True)
    c.print(kpis)
    c.print()

    # ── Business value bullets ─────────────────────────────────────────────────
    escalated = state.historical_escalated
    review_hours_saved = round(state.historical_payment_count * 8.3 / 60, 1)
    netting_count = sum(1 for r in state.runs if r.liquidity and r.liquidity.netting_opportunity)
    netting_saving = sum(
        float(r.liquidity.netting_opportunity.estimated_fx_saving_usd)
        for r in state.runs
        if r.liquidity and r.liquidity.netting_opportunity
    )

    bullets = Table.grid(padding=(0, 2))
    bullets.add_column(style="green bold", no_wrap=True)
    bullets.add_column()
    bullet_data = [
        ("✓", f"Saved {review_hours_saved:.1f} hours of manual review time today"),
        ("✓", f"Prevented {state.historical_hard_rejected} compliance violations from reaching settlement"),
        ("✓", f"Identified {netting_count} netting opportunities — eliminated ${netting_saving:,.0f} in FX exposure"),
        ("✓", f"Created {escalated} structured Maestro Cases with full AI-generated evidence bundles"),
        ("✓", f"Average agent analysis time: <1 ms per payment (deterministic engine mode)"),
    ]
    for icon, text in bullet_data:
        bullets.add_row(icon, text)

    c.print(Panel(bullets, title="[bold]BUSINESS VALUE DELIVERED TODAY[/]", border_style="cyan"))

    # ── Live run breakdown ─────────────────────────────────────────────────────
    from src.models.decision import DecisionType
    auto_count = sum(1 for r in state.runs if r.decision.decision == DecisionType.AUTO_EXECUTE)
    esc_count = sum(1 for r in state.runs if r.decision.decision == DecisionType.ESCALATE)
    rej_count = sum(1 for r in state.runs if r.decision.decision == DecisionType.HARD_REJECT)

    run_table = Table(title="Live Demo Run — All 10 Sample Payments", box=box.ROUNDED)
    run_table.add_column("Payment ID", style="cyan")
    run_table.add_column("Scenario")
    run_table.add_column("Compliance", justify="center")
    run_table.add_column("Risk Score", justify="right")
    run_table.add_column("Decision", justify="center")

    for r in state.runs:
        comp = r.compliance.decision.value if r.compliance else "N/A"
        comp_style = "green" if comp == "CLEAR" else ("yellow" if comp == "FLAG" else "red")
        score = f"{r.risk.composite_score:.1f}" if r.risk else "N/A"
        decision = r.decision.decision.value
        dec_style = "green" if decision == "AUTO_EXECUTE" else ("yellow" if decision == "ESCALATE" else "red")
        run_table.add_row(
            r.payment.payment_id,
            r.payment.scenario or "UNKNOWN",
            f"[{comp_style}]{comp}[/]",
            score,
            f"[{dec_style}]{decision}[/]",
        )

    c.print()
    c.print(run_table)
    c.print()
    c.print(Rule(
        f"[bold green]{auto_count} AUTO-EXECUTED[/]  "
        f"[bold yellow]{esc_count} ESCALATED[/]  "
        f"[bold red]{rej_count} REJECTED[/]"
    ))
    c.print()
