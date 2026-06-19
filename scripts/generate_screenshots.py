"""Screenshot generator — exports each dashboard screen as HTML and SVG.

Uses Rich's Console(record=True) mode to capture rendered output, then saves
to demo_output/ for inclusion in slide decks, README, and submission docs.

Usage:
  python scripts/generate_screenshots.py          # Export all screens
  python scripts/generate_screenshots.py --screen cfo  # Single screen
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure UTF-8 and correct path when run as a script
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import click
from rich.console import Console
from rich.rule import Rule

from src.core.logging_config import configure_logging

configure_logging("WARNING")

_OUTPUT_DIR = _ROOT / "demo_output"
_OUTPUT_DIR.mkdir(exist_ok=True)


def _make_recording_console(width: int = 140) -> Console:
    return Console(record=True, width=width, legacy_windows=False)


def _save(console: Console, stem: str) -> None:
    html_path = _OUTPUT_DIR / f"{stem}.html"
    svg_path = _OUTPUT_DIR / f"{stem}.svg"
    console.save_html(str(html_path))
    try:
        console.save_svg(str(svg_path), title=f"OmniTreasury AI — {stem.replace('_', ' ').title()}")
    except Exception:
        pass  # SVG export may fail on some Rich versions; HTML always works
    print(f"  Saved: {html_path.name}")


def _build_state():
    from src.utils.demo_generator import build_demo_state
    print("  Building demo state (running full pipeline)...")
    return build_demo_state(verbose=False)


def export_cfo(state=None) -> None:
    state = state or _build_state()
    c = _make_recording_console()
    from src.dashboard.cfo_dashboard import print_cfo_dashboard
    print_cfo_dashboard(state, c)
    _save(c, "01_cfo_command_center")


def export_executive_summary(state=None) -> None:
    state = state or _build_state()
    c = _make_recording_console()
    from src.dashboard.executive_summary import print_executive_summary
    print_executive_summary(state, c)
    _save(c, "02_executive_summary")


def export_risk_heatmap(state=None) -> None:
    state = state or _build_state()
    c = _make_recording_console()
    from src.dashboard.risk_heatmap import print_risk_heatmap
    print_risk_heatmap(state, c)
    _save(c, "03_risk_heatmap")


def export_liquidity(state=None) -> None:
    state = state or _build_state()
    c = _make_recording_console()
    from src.dashboard.liquidity_overview import print_liquidity_overview
    print_liquidity_overview(state, c)
    _save(c, "04_liquidity_overview")


def export_fx_report(state=None) -> None:
    state = state or _build_state()
    c = _make_recording_console()
    from src.dashboard.fx_report import print_fx_report
    print_fx_report(state, c)
    _save(c, "05_fx_savings_report")


def export_maestro(state=None) -> None:
    state = state or _build_state()
    c = _make_recording_console()
    from src.dashboard.maestro_dashboard import print_maestro_dashboard
    print_maestro_dashboard(state, c)
    _save(c, "06_maestro_cases")


def export_audit(state=None) -> None:
    state = state or _build_state()
    c = _make_recording_console()
    from src.dashboard.audit_timeline import print_audit_timeline
    print_audit_timeline(state, c)
    _save(c, "07_audit_timeline")


def export_all() -> None:
    print(f"\nOmniTreasury AI — Screenshot Generator")
    print(f"Output directory: {_OUTPUT_DIR}\n")

    state = _build_state()
    screens = [
        ("CFO Command Center", lambda: export_cfo(state)),
        ("Executive Summary", lambda: export_executive_summary(state)),
        ("Risk Heatmap", lambda: export_risk_heatmap(state)),
        ("Liquidity Overview", lambda: export_liquidity(state)),
        ("FX Savings Report", lambda: export_fx_report(state)),
        ("Maestro Cases", lambda: export_maestro(state)),
        ("Audit Timeline", lambda: export_audit(state)),
    ]
    for name, fn in screens:
        print(f"  Exporting: {name}")
        fn()

    html_files = sorted(_OUTPUT_DIR.glob("*.html"))
    print(f"\n  {len(html_files)} HTML files exported to {_OUTPUT_DIR}/")
    print("  Open any .html file in a browser to view the screenshot.\n")


@click.command()
@click.option(
    "--screen",
    default="all",
    type=click.Choice(["all", "cfo", "summary", "risk", "liquidity", "fx", "maestro", "audit"]),
    help="Which screen to export",
)
def main(screen: str) -> None:
    """Export OmniTreasury AI dashboard screens as HTML/SVG."""
    if screen == "all":
        export_all()
        return

    state = _build_state()
    dispatch = {
        "cfo": export_cfo,
        "summary": export_executive_summary,
        "risk": export_risk_heatmap,
        "liquidity": export_liquidity,
        "fx": export_fx_report,
        "maestro": export_maestro,
        "audit": export_audit,
    }
    dispatch[screen](state)


if __name__ == "__main__":
    main()
