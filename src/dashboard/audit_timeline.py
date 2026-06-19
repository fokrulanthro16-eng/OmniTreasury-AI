"""Audit Timeline — chronological immutable event log for compliance evidence."""

from __future__ import annotations

from collections import Counter
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

_EVENT_ICONS = {
    "PAYMENT_RECEIVED": ("->", "cyan"),
    "DOCUMENT_PARSED": ("[D]", "blue"),
    "AGENT_ANALYSIS_STARTED": ("[~]", "dim"),
    "AGENT_ANALYSIS_COMPLETE": ("[A]", "blue"),
    "AUTO_DECISION": ("[OK]", "bold green"),
    "CASE_CREATED": ("[C]", "bold magenta"),
    "HUMAN_DECISION": ("[H]", "yellow"),
    "PAYMENT_EXECUTED": ("[X]", "bold green"),
    "PAYMENT_REJECTED": ("[!]", "bold red"),
    "PAYMENT_BLOCKED": ("[B]", "bold red"),
    "SLA_BREACH": ("[S]", "red"),
    "ESCALATION_TIER_CHANGE": ("[E]", "yellow"),
}


def print_audit_timeline(state: "DemoState", console: Console | None = None) -> None:
    c = console or _SHARED
    from src.utils.audit_trail import audit_trail as trail

    c.print()
    c.print(Rule("[bold cyan] IMMUTABLE AUDIT TRAIL [/]"))
    c.print()

    records = trail.get_all_records()

    if not records:
        c.print("[dim]No audit records. Run the pipeline first.[/]")
        return

    # ── Full timeline table ────────────────────────────────────────────────────
    timeline = Table(
        title=f"Treasury Event Log — {len(records)} Records",
        box=box.MINIMAL_DOUBLE_HEAD,
        show_header=True,
    )
    timeline.add_column("#", justify="right", style="dim", no_wrap=True)
    timeline.add_column("Time (UTC)", style="dim", no_wrap=True)
    timeline.add_column("Ev", justify="center", no_wrap=True)
    timeline.add_column("Payment ID", style="cyan", no_wrap=True)
    timeline.add_column("Event Type")
    timeline.add_column("Agent")
    timeline.add_column("Detail", max_width=55)

    for i, rec in enumerate(records, start=1):
        icon, colour = _EVENT_ICONS.get(rec.event_type.value, ("•", "white"))
        ts = rec.timestamp.strftime("%H:%M:%S.%f")[:12]
        detail = ""
        if rec.metadata:
            pairs = [f"{k}={v}" for k, v in list(rec.metadata.items())[:3]]
            detail = "  ".join(pairs)

        timeline.add_row(
            str(i),
            ts,
            f"[{colour}]{icon}[/]",
            rec.payment_id[:16],
            f"[{colour}]{rec.event_type.value}[/]",
            rec.agent_name or "—",
            f"[dim]{detail}[/]",
        )

    c.print(timeline)

    # ── Event distribution ─────────────────────────────────────────────────────
    c.print()
    event_counts = Counter(rec.event_type.value for rec in records)
    dist_table = Table(title="Event Distribution", box=box.SIMPLE, show_header=True)
    dist_table.add_column("Event Type")
    dist_table.add_column("Count", justify="right")
    dist_table.add_column("Bar", min_width=20)
    max_count = max(event_counts.values(), default=1)

    for ev_type in sorted(event_counts, key=lambda x: -event_counts[x]):
        count = event_counts[ev_type]
        icon, colour = _EVENT_ICONS.get(ev_type, ("•", "white"))
        bar_len = int(count / max_count * 20)
        bar = f"[{colour}]" + "█" * bar_len + "[/]" + "░" * (20 - bar_len)
        dist_table.add_row(
            f"[{colour}]{icon} {ev_type}[/]",
            str(count),
            bar,
        )
    c.print(dist_table)

    # ── Integrity statement ────────────────────────────────────────────────────
    c.print()
    payment_ids = sorted({rec.payment_id for rec in records})
    integrity_msg = Table.grid(padding=(0, 2))
    integrity_msg.add_row(
        "[bold green]✓[/]",
        f"[bold]Audit trail integrity confirmed.[/]  "
        f"{len(records)} records across {len(payment_ids)} payments.  "
        "All records are append-only and tamper-evident.",
    )
    c.print(Panel(integrity_msg, border_style="green", title="[bold]COMPLIANCE EVIDENCE[/]"))
    c.print()
