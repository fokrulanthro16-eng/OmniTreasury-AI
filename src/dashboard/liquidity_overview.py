"""Global Liquidity Overview — multi-entity cash position table."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
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
_DATA_PATH = Path(__file__).resolve().parents[2] / "sample_data" / "liquidity_positions.json"


def _headroom_bar(headroom_pct: float, width: int = 12) -> str:
    filled = max(0, min(width, int(headroom_pct / 100 * width)))
    bar = "█" * filled + "░" * (width - filled)
    return bar


def _format_amount(amount: Decimal | float, currency: str) -> str:
    v = float(amount)
    if abs(v) >= 1_000_000:
        return f"{currency} {v/1_000_000:.2f}M"
    if abs(v) >= 1_000:
        return f"{currency} {v/1_000:.1f}K"
    return f"{currency} {v:,.0f}"


def print_liquidity_overview(state: "DemoState | None" = None, console: Console | None = None) -> None:
    c = console or _SHARED

    raw = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    positions = raw.get("positions", {})

    c.print()
    c.print(Rule("[bold cyan] GLOBAL LIQUIDITY OVERVIEW [/]"))
    c.print()

    table = Table(
        title="Cash Positions — All Entities & Currencies",
        box=box.ROUNDED,
        show_footer=True,
    )
    table.add_column("Entity", style="bold cyan", footer="[bold]TOTAL[/]")
    table.add_column("Currency", justify="center")
    table.add_column("Available Balance", justify="right")
    table.add_column("Covenant Min", justify="right", style="dim")
    table.add_column("Headroom", justify="right")
    table.add_column("Utilisation", justify="center", footer="")
    table.add_column("Status", justify="center")

    total_usd_equiv = Decimal("0")
    # Approximate FX rates for display
    fx_to_usd = {"EUR": Decimal("1.085"), "USD": Decimal("1.0"), "GBP": Decimal("1.265"),
                 "SGD": Decimal("0.74"), "JPY": Decimal("0.0067")}

    for key, pos in positions.items():
        avail = Decimal(str(pos["available_balance"]))
        total = Decimal(str(pos["total_balance"]))
        cov_min = Decimal(str(pos.get("covenant_minimum", 0)))
        headroom = avail - cov_min
        utilisation = float((total - avail) / total * 100) if total > 0 else 0.0
        headroom_pct = float(headroom / total * 100) if total > 0 else 0.0

        currency = pos["currency"]
        rate = fx_to_usd.get(currency, Decimal("1.0"))
        total_usd_equiv += avail * rate

        # Status coloring
        if avail < cov_min:
            status = "[bold red]BREACH[/]"
            avail_str = f"[red]{_format_amount(avail, currency)}[/]"
            headroom_str = f"[red]{_format_amount(headroom, currency)}[/]"
        elif headroom < cov_min * Decimal("0.2"):
            status = "[bold yellow]CAUTION[/]"
            avail_str = f"[yellow]{_format_amount(avail, currency)}[/]"
            headroom_str = f"[yellow]{_format_amount(headroom, currency)}[/]"
        else:
            status = "[bold green]OK[/]"
            avail_str = _format_amount(avail, currency)
            headroom_str = f"[green]{_format_amount(headroom, currency)}[/]"

        util_colour = "red" if utilisation > 80 else ("yellow" if utilisation > 60 else "green")
        util_str = f"[{util_colour}]{utilisation:.0f}%[/]  {_headroom_bar(headroom_pct)}"

        table.add_row(
            pos["entity"],
            currency,
            avail_str,
            _format_amount(cov_min, currency),
            headroom_str,
            util_str,
            status,
        )

    c.print(table)

    # ── Consolidated summary ───────────────────────────────────────────────────
    c.print()
    summary = Table.grid(padding=(0, 4))
    summary.add_row(
        f"[bold cyan]Consolidated USD Equivalent:[/] [bold]${float(total_usd_equiv):>14,.0f}[/]",
        f"[bold cyan]Entities Monitored:[/] [bold]{len(positions)}[/]",
        f"[bold cyan]Covenant Breaches:[/] [bold green]NONE[/]",
    )
    c.print(Panel(summary, border_style="dim"))

    # ── Netting opportunities ──────────────────────────────────────────────────
    netting = raw.get("netting_candidates", [])
    if netting:
        c.print()
        net_table = Table(title="Active Intercompany Netting Opportunities", box=box.SIMPLE)
        net_table.add_column("Counterparty", style="cyan")
        net_table.add_column("Currency", justify="center")
        net_table.add_column("Offsetting Amount", justify="right")
        net_table.add_column("Description")
        for n in netting:
            net_table.add_row(
                n["counterparty"],
                n["currency"],
                _format_amount(Decimal(str(n["amount"])), n["currency"]),
                n.get("description", ""),
            )
        c.print(net_table)

    c.print()
