"""General utility helpers used across OmniTreasury AI."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from src.models.decision import DecisionResult, DecisionType
from src.models.payment import PaymentRecord

console = Console(legacy_windows=False)


def format_currency(amount: Decimal | float, currency: str) -> str:
    return f"{currency} {float(amount):>14,.2f}"


def print_payment_header(payment: PaymentRecord) -> None:
    console.print(Panel(
        f"[bold cyan]Payment ID:[/] {payment.payment_id}\n"
        f"[bold cyan]Amount    :[/] {format_currency(payment.amount, payment.source_currency)} "
        f"→ {payment.target_currency}\n"
        f"[bold cyan]Counterpty:[/] {payment.counterparty.name} ({payment.counterparty.bank_country})\n"
        f"[bold cyan]Purpose   :[/] {payment.purpose.value}\n"
        f"[bold cyan]Reference :[/] {payment.reference}\n"
        f"[bold cyan]Value Date:[/] {payment.value_date}",
        title="[bold white]PAYMENT UNDER ANALYSIS[/]",
        border_style="cyan",
    ))


def print_decision_result(decision: DecisionResult) -> None:
    colour_map = {
        DecisionType.AUTO_EXECUTE: "green",
        DecisionType.ESCALATE: "yellow",
        DecisionType.HARD_REJECT: "red",
    }
    colour = colour_map.get(decision.decision, "white")
    icon_map = {
        DecisionType.AUTO_EXECUTE: "✓ AUTO-EXECUTE",
        DecisionType.ESCALATE: "⚠ ESCALATE",
        DecisionType.HARD_REJECT: "✗ HARD REJECT",
    }
    icon = icon_map.get(decision.decision, decision.decision.value)

    body_lines = [f"[bold {colour}]{icon}[/]", f"\n{decision.summary}"]

    if decision.escalation_level:
        body_lines.append(f"\n[bold]Assigned to:[/] {decision.escalation_level.value}")
    if decision.execution_route:
        body_lines.append(f"\n[bold]FX Provider:[/] {decision.execution_route}")

    console.print(Panel(
        "\n".join(body_lines),
        title=f"[bold {colour}]TREASURY DECISION[/]",
        border_style=colour,
    ))

    if decision.rationales:
        table = Table(title="Decision Rationales", box=box.SIMPLE)
        table.add_column("Trigger", style="bold")
        table.add_column("Agent")
        table.add_column("Description")
        for r in decision.rationales:
            table.add_row(r.trigger, r.agent_source, r.description[:80] + ("..." if len(r.description) > 80 else ""))
        console.print(table)


def print_agent_summary_table(
    compliance_decision: str,
    fx_savings: Decimal,
    liquidity_status: str,
    risk_score: float,
) -> None:
    table = Table(title="Agent Analysis Summary", box=box.ROUNDED)
    table.add_column("Agent", style="bold cyan")
    table.add_column("Result")
    table.add_column("Key Finding")

    compliance_colour = "green" if compliance_decision == "CLEAR" else "red"
    table.add_row(
        "Compliance Auditor",
        f"[{compliance_colour}]{compliance_decision}[/]",
        "Screening complete",
    )
    table.add_row(
        "Forex Strategist",
        f"[green]${float(fx_savings):,.2f} saved[/]",
        "Best route identified",
    )
    liq_colour = "green" if liquidity_status == "SUFFICIENT" else "yellow"
    table.add_row(
        "Liquidity Balancer",
        f"[{liq_colour}]{liquidity_status}[/]",
        "Position validated",
    )
    risk_colour = "green" if risk_score < 40 else ("yellow" if risk_score < 60 else "red")
    table.add_row(
        "Risk Intelligence",
        f"[{risk_colour}]Score: {risk_score:.1f}[/]",
        "Risk factors assessed",
    )
    console.print(table)


def utcnow_str() -> str:
    return datetime.utcnow().isoformat() + "Z"
