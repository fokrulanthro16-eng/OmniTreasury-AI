"""Cases router — Maestro escalation case lifecycle management.

GET  /api/cases              list all cases (optional ?status= filter)
GET  /api/cases/{case_id}    fetch a single case
PATCH /api/cases/{case_id}   update status / reviewer / notes
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.web import store

router = APIRouter()

_VALID_STATUSES = {"OPEN", "UNDER_REVIEW", "APPROVED", "REJECTED", "CLOSED"}

# Status transitions allowed from each state
_TRANSITIONS: dict[str, set[str]] = {
    "OPEN":         {"UNDER_REVIEW"},
    "UNDER_REVIEW": {"APPROVED", "REJECTED"},
    "APPROVED":     {"CLOSED"},
    "REJECTED":     {"CLOSED"},
    "CLOSED":       set(),
}


class CaseUpdate(BaseModel):
    status: Optional[str] = None
    reviewer: Optional[str] = None
    reviewer_notes: Optional[str] = None


@router.get("/cases")
def list_cases(status: Optional[str] = None):
    """Return all Maestro cases, newest first. Filter by ?status= if given."""
    return store.list_cases(status=status)


@router.get("/cases/{case_id}")
def get_case(case_id: str):
    case = store.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    return case


@router.patch("/cases/{case_id}")
def update_case(case_id: str, body: CaseUpdate):
    """Update case status, reviewer, and/or notes. Validates status transitions."""
    case = store.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    prev_status = case.get("status", "OPEN")

    if body.status:
        new_status = body.status.upper()
        if new_status not in _VALID_STATUSES:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid status '{new_status}'. Valid: {sorted(_VALID_STATUSES)}",
            )
        allowed = _TRANSITIONS.get(prev_status, set())
        if new_status != prev_status and new_status not in allowed:
            raise HTTPException(
                status_code=422,
                detail=f"Cannot transition from {prev_status} to {new_status}. "
                       f"Allowed: {sorted(allowed) or 'none'}",
            )
        case["status"] = new_status

    now = datetime.now(timezone.utc).isoformat()
    if body.reviewer is not None:
        case["reviewer"] = body.reviewer
    if body.reviewer_notes is not None:
        case["reviewer_notes"] = body.reviewer_notes
    case["updated_at"] = now

    final_status = case.get("status", prev_status)
    if final_status in {"APPROVED", "REJECTED", "CLOSED"} and not case.get("closed_at"):
        case["closed_at"] = now

    store.upsert_case(case)

    # Determine audit event type
    if final_status in {"APPROVED", "REJECTED"}:
        event_type = "CASE_DECISION"
        desc = (
            f"Case {case_id} {final_status.lower()} by "
            f"{body.reviewer or case.get('reviewer', 'reviewer')}"
        )
    elif final_status == "UNDER_REVIEW":
        event_type = "CASE_UPDATED"
        desc = f"Case {case_id} moved to UNDER_REVIEW"
    elif final_status == "CLOSED":
        event_type = "CASE_UPDATED"
        desc = f"Case {case_id} closed"
    else:
        event_type = "CASE_UPDATED"
        desc = f"Case {case_id} updated"

    store.add_audit(
        event_type=event_type,
        description=desc,
        actor=body.reviewer or case.get("reviewer") or "system",
        upload_id=case.get("upload_id"),
        case_id=case_id,
        details={
            "previous_status": prev_status,
            "new_status":      final_status,
            "reviewer":        body.reviewer,
            "notes":           body.reviewer_notes,
        },
    )

    return {"success": True, "case": case}
