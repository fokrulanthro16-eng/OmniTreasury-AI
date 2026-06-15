"""CFO Command Center — the primary at-a-glance dashboard combining all signals."""

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


def _metric_panel(label: str, value: str, sub: str, colour: str = "cyan") -> Panel:
    body = Text(justify="center")
    body.append("\n")
    body.append(value, style=f"bold {colour}")
    body.append(f"\n{sub}", style="dim")
    body.append("\n")
    return Panel(body, title=f"[dim]{label}[/]", border_style=colour, expand=True, padding=(0, 1))


def print_cfo_dashboard(state: "DemoState", console: Console | None = None) -> None:
    c = console or _SHARED
    from src.models.decision import DecisionType

    now_str = datetime.utcnow().strftime("%A, %d %B %Y  %H:%M UTC")

    c.print()
    c.print(Rule(f"[bold cyan] OMNITREASURY AI — CFO COMMAND CENTER  ·  {now_str} [/]"))
    c.print()

    # ── KPI strip ──────────────────────────────────────────────────────────────
    auto_count = sum(1 for r in state.runs if r.decision.decision == DecisionType.AUTO_EXECUTE)
    esc_count = sum(1 for r in state.runs if r.decision.decision == DecisionType.ESCALATE)
    rej_count = sum(1 for r in state.runs if r.decision.decision == DecisionType.HARD_REJECT)
    total_fx_savings = sum(r.fx.estimated_savings_usd for r in state.runs if r.fx)
    avg_risk = (
        sum(r.risk.composite_score for r in state.runs if r.risk)
        / max(sum(1 for r in state.runs if r.risk), 1)
    )
    auto_pct = int(state.historical_auto_executed / max(state.historical_payment_count, 1) * 100)

    kpi_row = Columns([
        _metric_panel(
            "PAYMENTS TODAY",
            str(state.historical_payment_count),
            f"${state.historical_total_value_m:.1f}M total value",
            "cyan",
        ),
        _metric_panel(
            "AUTOMATION RATE",
            f"{auto_pct}%",
            f"{state.historical_auto_executed} auto / {state.historical_escalated} escalated",
            "green",
        ),
        _metric_panel(
            "FX SAVINGS",
            f"${float(state.historical_fx_savings_usd):,.0f}",
            f"YTD  |  +${float(total_fx_savings):,.0f} this run",
            "yellow",
        ),
        _metric_panel(
            "AVG RISK SCORE",
            f"{avg_risk:.1f}",
            f"{'LOW' if avg_risk < 40 else 'MEDIUM' if avg_risk < 60 else 'HIGH'} risk portfolio",
            "green" if avg_risk < 40 else "yellow",
        ),
        _metric_panel(
            "MAESTRO CASES",
            str(state.historical_escalated),
            f"{esc_count} from live run",
            "magenta",
        ),
    ], equal=True, expand=True)
    c.print(kpi_row)
    c.print()

    # ── Active Cases + Risk Alerts side-by-side ────────────────────────────────
    escalated = [r for r in state.runs if r.decision.decision == DecisionType.ESCALATE]

    cases_table = Table(title="Active Maestro Cases", box=box.ROUNDED, expand=True)
    cases_table.add_column("Case", style="bold magenta", no_wrap=True)
    cases_table.add_column("Assigned To")
    cases_table.add_column("Payment ID", style="cyan")
    cases_table.add_column("SLA", justify="right")

    _esc_label = {
        "COMPLIANCE_OFFICER": "[yellow]Compliance[/]",
        "TREASURY_MANAGER": "[cyan]Treasury Mgr[/]",
        "CFO": "[bold red]CFO[/]",
        "LEGAL": "[magenta]Legal[/]",
    }
    from datetime import timedelta
    for i, run in enumerate(escalated[:6], start=1):
        esc_level = run.decision.escalation_level
        level_str = _esc_label.get(esc_level.value if esc_level else "", "Unknown")
        from src.dashboard.maestro_dashboard import _SLA_BY_LEVEL, _sla_remaining
        sla_mins = _SLA_BY_LEVEL.get(esc_level.value if esc_level else "", 240)
        created = datetime.utcnow() - timedelta(minutes=i * 23 + 7)
        sla_str = _sla_remaining(created, sla_mins)
        cases_table.add_row(
            f"CASE-{2040 + i:04d}",
            level_str,
            run.payment.payment_id,
            sla_str,
        )

    risk_table = Table(title="Risk Alerts", box=box.ROUNDED, expand=True)
    risk_table.add_column("Payment ID", style="cyan")
    risk_table.add_column("Score", justify="right")
    risk_table.add_column("Level", justify="center")
    risk_table.add_column("Counterparty", max_width=22)

    high_risk = sorted(
        [r for r in state.runs if r.risk],
        key=lambda r: r.risk.composite_score,
        reverse=True,
    )[:6]
    for run in high_risk:
        r = run.risk
        lvl = r.risk_level.value
        colour = "red" if lvl in ("HIGH", "CRITICAL") else "yellow"
        risk_table.add_row(
            run.payment.payment_id,
            f"[{colour}]{r.composite_score:.1f}[/]",
            f"[{colour}]{lvl}[/]",
            run.payment.counterparty.name[:22],
        )

    c.print(Columns([cases_table, risk_table], equal=True, expand=True))
    c.print()

    # ── Live run summary strip ─────────────────────────────────────────────────
    from src.models.compliance import ComplianceDecision
    compliance_clear = sum(
        1 for r in state.runs
        if r.compliance and r.compliance.decision == ComplianceDecision.CLEAR
    )
    netting_ops = sum(1 for r in state.runs if r.liquidity and r.liquidity.netting_opportunity)

    strip = Table.grid(padding=(0, 6))
    strip.add_row(
        f"[bold]Live Run Outcomes:[/]  "
        f"[green]{auto_count} AUTO-EXEC[/]  "
        f"[yellow]{esc_count} ESCALATED[/]  "
        f"[red]{rej_count} REJECTED[/]",
        f"[bold]Compliance:[/]  [green]{compliance_clear}/{len(state.runs)} CLEAR[/]",
        f"[bold]Netting Opportunities:[/]  [yellow]{netting_ops} found[/]",
        f"[bold]Agent Mode:[/]  [dim]Engine (no LLM key needed)[/]",
    )
    c.print(Panel(strip, border_style="dim"))
    c.print()
