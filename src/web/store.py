"""Persistent data store for Maestro cases and audit trail.

Thread-safe, file-backed JSON repositories under data/.
All write paths use a single lock per store type.
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = _ROOT / "data"
CASES_FILE = DATA_DIR / "cases.json"
AUDIT_FILE  = DATA_DIR / "audit.json"

_CASE_LOCK  = threading.Lock()
_AUDIT_LOCK = threading.Lock()


def _ensure() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _read(path: Path) -> list[dict]:
    _ensure()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _write(path: Path, records: list[dict], max_items: int = 2000) -> None:
    _ensure()
    path.write_text(
        json.dumps(records[:max_items], indent=2, default=str),
        encoding="utf-8",
    )


# ── Case repository ───────────────────────────────────────────────────────────

def list_cases(status: Optional[str] = None) -> list[dict]:
    """Return all cases, newest first. Optionally filter by status."""
    cases = _read(CASES_FILE)
    if status:
        cases = [c for c in cases if c.get("status") == status.upper()]
    return cases


def get_case(case_id: str) -> Optional[dict]:
    return next((c for c in _read(CASES_FILE) if c.get("case_id") == case_id), None)


def upsert_case(record: dict) -> None:
    """Insert or replace a case (matched on case_id). Prepends so newest is first."""
    with _CASE_LOCK:
        records = _read(CASES_FILE)
        records = [r for r in records if r.get("case_id") != record["case_id"]]
        records.insert(0, record)
        _write(CASES_FILE, records)


# ── Audit repository ──────────────────────────────────────────────────────────

def list_audit(
    limit: int = 200,
    upload_id: Optional[str] = None,
    case_id: Optional[str] = None,
) -> list[dict]:
    """Return audit events newest-first, with optional filters."""
    events = _read(AUDIT_FILE)
    if upload_id:
        events = [e for e in events if e.get("upload_id") == upload_id]
    if case_id:
        events = [e for e in events if e.get("case_id") == case_id]
    return events[:limit]


def add_audit(
    event_type: str,
    description: str,
    actor: str = "system",
    upload_id: Optional[str] = None,
    case_id: Optional[str] = None,
    details: Optional[dict] = None,
) -> str:
    """Append an immutable audit event. Returns the new event_id."""
    event: dict = {
        "event_id":   str(uuid.uuid4()),
        "event_type": event_type,
        "timestamp":  datetime.now(timezone.utc).isoformat(),
        "actor":      actor,
        "upload_id":  upload_id,
        "case_id":    case_id,
        "description": description,
        "details":    details or {},
    }
    with _AUDIT_LOCK:
        events = _read(AUDIT_FILE)
        events.insert(0, event)
        _write(AUDIT_FILE, events, max_items=5000)
    return event["event_id"]
