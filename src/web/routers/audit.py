"""Audit trail router — GET /api/audit."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

from src.web import store

router = APIRouter()


@router.get("/audit")
def list_audit(
    limit: int = 100,
    upload_id: Optional[str] = None,
    case_id: Optional[str] = None,
):
    """Return audit events newest-first. Optional filters: upload_id, case_id."""
    return store.list_audit(limit=limit, upload_id=upload_id, case_id=case_id)
