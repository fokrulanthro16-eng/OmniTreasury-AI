"""Risk Heatmap — counterparty × risk dimension matrix with colour coding."""

from __future__ import annotations

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

_RISK_DIMS = [
    ("CPTY", "Counterparty"),
    ("CONC", "Concentration"),
    ("MKT", "Market"),
    ("OPS", "Operational"),
    ("SETT", "Settlement"),
]


def _score_to_cell(score: float) -> Text:
    if score >= 75:
        label = f"{score:>5.1f}"
        return Text(label, style="bold white on red")
    if score >= 55:
        label = f"{score:>5.1f}"
        return Text(label, style="bold black on yellow")
    if score >= 35:
        label = f"{score:>5.1f}"
        return Text(label, style="bold white on dark_orange")
    label = f"{score:>5.1f}"
    return Text(label, style="bold black on green")


def _risk_level_style(level: str) -> str:
    return {
        "LOW": "green",
        "MEDIUM": "yellow",
        "HIGH": "red",
        "CRITICAL": "bold red",
    }.get(level, "white")


def print_risk_heatmap(state: "DemoState", console: Console | None = None) -> None:
    c = console or _SHARED

    c.print()
    c.print(Rule("[bold red] RISK INTELLIGENCE HEATMAP [/]"))
    c.print()

    # ── Counterparty × dimension matrix ───────────────────────────────────────
    heat_table = Table(
        title="Risk Score Matrix — Counterparty vs Dimension (0-100)",
        box=box.ROUNDED,
        show_header=True,
    )
    heat_table.add_column("Payment / Counterparty", style="bold", min_width=30, no_wrap=True)
    heat_table.add_column("Composite", justify="center", min_width=10)
    for abbr, label in _RISK_DIMS:
        heat_table.add_column(abbr, justify="center", min_width=7, header_style="bold cyan")
    heat_table.add_column("Level", justify="center")
    heat_table.add_column("Flags", justify="left")

    # Sort runs by composite risk score descending
    sorted_runs = sorted(state.runs, key=lambda r: r.risk.composite_score if r.risk else 0, reverse=True)

    for run in sorted_runs:
        r = run.risk
        if not r:
            continue

        # Extract factor scores by category
        factor_by_cat: dict[str, float] = {}
        for factor in r.factors:
            factor_by_cat[factor.category.value] = factor.score

        dim_cells = [
            _score_to_cell(factor_by_cat.get("COUNTERPARTY", 0.0)),
            _score_to_cell(factor_by_cat.get("CONCENTRATION", 0.0)),
            _score_to_cell(factor_by_cat.get("MARKET", 0.0)),
            _score_to_cell(factor_by_cat.get("OPERATIONAL", 0.0)),
            _score_to_cell(factor_by_cat.get("SETTLEMENT", 0.0)),
        ]

        flags = ", ".join(r.limit_breaches[:2]) if r.limit_breaches else "—"
        level_style = _risk_level_style(r.risk_level.value)
        cpty_name = run.payment.counterparty.name[:26]

        heat_table.add_row(
            f"{run.payment.payment_id}  {cpty_name:<20}",
            _score_to_cell(r.composite_score),
            *dim_cells,
            f"[{level_style}]{r.risk_level.value}[/]",
            f"[dim]{flags}[/]",
        )

    c.print(heat_table)
    c.print()

    # ── Legend ─────────────────────────────────────────────────────────────────
    legend = Table.grid(padding=(0, 3))
    legend.add_row(
        Text("  0-34  ", style="bold black on green"),
        Text(" LOW ", style="green"),
        Text("  35-54  ", style="bold white on dark_orange"),
        Text(" MODERATE ", style="dark_orange"),
        Text("  55-74  ", style="bold black on yellow"),
        Text(" HIGH ", style="yellow"),
        Text("  75+   ", style="bold white on red"),
        Text(" CRITICAL ", style="red"),
    )
    c.print(Panel(legend, title="[bold]Score Legend[/]", border_style="dim", expand=False))

    # ── Top risk alerts ────────────────────────────────────────────────────────
    high_risk_runs = [r for r in state.runs if r.risk and r.risk.composite_score >= 55]
    if high_risk_runs:
        c.print()
        alert_table = Table(title="Active Risk Alerts", box=box.SIMPLE)
        alert_table.add_column("Payment ID", style="bold")
        alert_table.add_column("Score", justify="right")
        alert_table.add_column("Level", justify="center")
        alert_table.add_column("Primary Risk Factor")
        alert_table.add_column("Recommendation")

        for run in sorted(high_risk_runs, key=lambda r: r.risk.composite_score, reverse=True)[:5]:
            r = run.risk
            top_factor = max(r.factors, key=lambda f: f.score, default=None) if r.factors else None
            factor_str = f"{top_factor.name}: {top_factor.score:.1f}" if top_factor else "N/A"
            rec = r.mitigation_recommendations[0] if r.mitigation_recommendations else "Escalate for manual review"
            level_style = _risk_level_style(r.risk_level.value)
            alert_table.add_row(
                run.payment.payment_id,
                f"[{level_style}]{r.composite_score:.1f}[/]",
                f"[{level_style}]{r.risk_level.value}[/]",
                factor_str,
                rec[:60] + ("..." if len(rec) > 60 else ""),
            )
        c.print(alert_table)

    c.print()
