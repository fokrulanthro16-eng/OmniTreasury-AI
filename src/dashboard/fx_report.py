"""FX Savings Report — provider comparison and savings leaderboard."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
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


def _savings_bar(savings: Decimal, max_savings: Decimal, width: int = 20) -> str:
    if max_savings <= 0:
        return "░" * width
    ratio = float(savings / max_savings)
    filled = max(0, min(width, int(ratio * width)))
    return "[green]" + "█" * filled + "[/]" + "░" * (width - filled)


def print_fx_report(state: "DemoState", console: Console | None = None) -> None:
    c = console or _SHARED

    c.print()
    c.print(Rule("[bold yellow] FX OPTIMISATION REPORT [/]"))
    c.print()

    runs_with_fx = [r for r in state.runs if r.fx]
    if not runs_with_fx:
        c.print("[yellow]No FX results available.[/]")
        return

    # ── Provider leaderboard ───────────────────────────────────────────────────
    provider_savings: dict[str, Decimal] = defaultdict(Decimal)
    provider_count: dict[str, int] = defaultdict(int)
    for run in runs_with_fx:
        fx = run.fx
        provider_savings[fx.recommended_provider] += fx.estimated_savings_usd
        provider_count[fx.recommended_provider] += 1

    prov_table = Table(title="FX Provider Leaderboard — Savings Generated", box=box.ROUNDED)
    prov_table.add_column("Provider", style="bold cyan")
    prov_table.add_column("Payments Routed", justify="center")
    prov_table.add_column("Total Savings (USD)", justify="right")
    prov_table.add_column("Avg Savings / Payment", justify="right")
    prov_table.add_column("Savings Bar", min_width=22)

    max_saving = max(provider_savings.values(), default=Decimal("1"))
    for prov, total in sorted(provider_savings.items(), key=lambda x: -x[1]):
        count = provider_count[prov]
        avg = total / count if count else Decimal("0")
        bar = _savings_bar(total, max_saving)
        prov_table.add_row(
            prov,
            str(count),
            f"[bold green]${float(total):>10,.2f}[/]",
            f"${float(avg):>8,.2f}",
            bar,
        )
    c.print(prov_table)

    # ── Currency pair breakdown ────────────────────────────────────────────────
    c.print()
    pair_savings: dict[str, Decimal] = defaultdict(Decimal)
    pair_count: dict[str, int] = defaultdict(int)
    pair_best_rate: dict[str, Decimal] = {}
    for run in runs_with_fx:
        fx = run.fx
        pair_savings[fx.currency_pair] += fx.estimated_savings_usd
        pair_count[fx.currency_pair] += 1
        if fx.currency_pair not in pair_best_rate or fx.recommended_rate > pair_best_rate[fx.currency_pair]:
            pair_best_rate[fx.currency_pair] = fx.recommended_rate

    pair_table = Table(title="Currency Pair Analysis", box=box.SIMPLE)
    pair_table.add_column("Pair", style="bold")
    pair_table.add_column("Transactions", justify="center")
    pair_table.add_column("Best Rate Achieved", justify="right")
    pair_table.add_column("Total Savings (USD)", justify="right")
    pair_table.add_column("Timing Signal", justify="center")

    for pair in sorted(pair_savings.keys()):
        savings = pair_savings[pair]
        timing_signals = [
            r.fx.timing_recommendation.value
            for r in runs_with_fx
            if r.fx.currency_pair == pair
        ]
        dominant_signal = max(set(timing_signals), key=timing_signals.count) if timing_signals else "N/A"
        signal_style = "green" if dominant_signal == "EXECUTE_NOW" else "yellow"

        pair_table.add_row(
            pair,
            str(pair_count[pair]),
            f"{float(pair_best_rate.get(pair, Decimal('0'))):>10.4f}",
            f"[green]${float(savings):>8,.2f}[/]",
            f"[{signal_style}]{dominant_signal.replace('_', ' ')}[/]",
        )
    c.print(pair_table)

    # ── Payment-level savings detail ───────────────────────────────────────────
    c.print()
    detail_table = Table(title="Per-Payment FX Optimisation Detail", box=box.MINIMAL_DOUBLE_HEAD)
    detail_table.add_column("Payment ID", style="cyan")
    detail_table.add_column("Pair")
    detail_table.add_column("Amount", justify="right")
    detail_table.add_column("Provider", style="bold")
    detail_table.add_column("Rate", justify="right")
    detail_table.add_column("Savings vs Benchmark", justify="right")
    detail_table.add_column("Savings bps", justify="right")
    detail_table.add_column("Hedge?", justify="center")

    for run in sorted(runs_with_fx, key=lambda r: r.fx.estimated_savings_usd, reverse=True):
        fx = run.fx
        has_hedge = "YES" if (fx.hedge_opportunity and fx.hedge_opportunity.recommended) else "—"
        hedge_style = "yellow" if has_hedge == "YES" else "dim"
        savings_style = "green" if fx.estimated_savings_usd > 0 else "dim"
        detail_table.add_row(
            run.payment.payment_id,
            fx.currency_pair,
            f"{float(fx.payment_amount):>12,.2f}",
            fx.recommended_provider,
            f"{float(fx.recommended_rate):.4f}",
            f"[{savings_style}]${float(fx.estimated_savings_usd):>8,.2f}[/]",
            f"{fx.savings_bps:.1f}",
            f"[{hedge_style}]{has_hedge}[/]",
        )
    c.print(detail_table)

    # ── Summary footer ─────────────────────────────────────────────────────────
    c.print()
    total_savings = sum(r.fx.estimated_savings_usd for r in runs_with_fx)
    avg_bps = sum(r.fx.savings_bps for r in runs_with_fx) / len(runs_with_fx)
    volatility_flagged = sum(1 for r in runs_with_fx if r.fx.volatility_flag)
    hedge_ops = sum(1 for r in runs_with_fx if r.fx and r.fx.hedge_opportunity)

    summary = Table.grid(padding=(0, 4))
    summary.add_row(
        f"[bold]Total FX Savings:[/]  [bold green]${float(total_savings):,.2f}[/]",
        f"[bold]Average Savings:[/]  [bold]{avg_bps:.1f} bps[/]",
        f"[bold]Volatility Alerts:[/]  [bold yellow]{volatility_flagged}[/]",
        f"[bold]Hedge Opportunities:[/]  [bold yellow]{hedge_ops}[/]",
    )
    c.print(Panel(summary, title="[bold]FX Summary[/]", border_style="yellow"))
    c.print()
