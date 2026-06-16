"""Metrics router — GET /api/metrics.

Aggregates live statistics from uploads, processing results, and cases.
"""

from __future__ import annotations

from fastapi import APIRouter

from src.web import history as hist, store

router = APIRouter()


@router.get("/metrics")
def get_metrics():
    """Return aggregate KPIs: STP rate, FX savings, risk scores, case counts."""
    uploads = hist.load()
    cases   = store.list_cases()

    total     = len(uploads)
    processed = [u for u in uploads if u.get("status") == "processed"]

    def _result(u: dict) -> dict:
        return u.get("processing_result") or {}

    swift_results = [r for u in processed if "decision" in _result(u) for r in [_result(u)]]
    decisions = [r["decision"]["decision"] for r in swift_results if r.get("decision")]

    auto_exec   = decisions.count("AUTO_EXECUTE")
    escalated   = decisions.count("ESCALATE")
    hard_reject = decisions.count("HARD_REJECT")
    stp_rate    = round(auto_exec / len(decisions), 3) if decisions else 0.0

    risk_scores = [
        r["risk"]["composite_score"]
        for r in swift_results
        if r.get("risk") and r["risk"].get("composite_score") is not None
    ]
    avg_risk = round(sum(risk_scores) / len(risk_scores), 1) if risk_scores else 0.0

    fx_savings = sum(
        r.get("forex", {}).get("estimated_savings_usd", 0)
        for r in swift_results
        if r.get("forex")
    )

    total_value = sum(
        r.get("payment", {}).get("amount", 0)
        for r in swift_results
        if r.get("payment")
    )

    case_by_status: dict[str, int] = {}
    for c in cases:
        s = c.get("status", "UNKNOWN")
        case_by_status[s] = case_by_status.get(s, 0) + 1

    return {
        "total_uploads":       total,
        "processed":           len(processed),
        "auto_execute":        auto_exec,
        "escalated":           escalated,
        "hard_reject":         hard_reject,
        "stp_rate":            stp_rate,
        "open_cases":          case_by_status.get("OPEN", 0),
        "under_review_cases":  case_by_status.get("UNDER_REVIEW", 0),
        "approved_cases":      case_by_status.get("APPROVED", 0),
        "rejected_cases":      case_by_status.get("REJECTED", 0),
        "total_cases":         len(cases),
        "avg_risk_score":      avg_risk,
        "total_value_processed": round(total_value, 2),
        "total_fx_savings":    round(fx_savings, 2),
    }
