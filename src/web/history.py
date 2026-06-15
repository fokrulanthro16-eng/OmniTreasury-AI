"""Upload history — thread-safe JSON persistence for upload records.

All routers share this module so there's exactly one write path
to ``sample_data/uploads/upload_history.json``.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Optional

_LOCK = threading.Lock()

_ROOT = Path(__file__).parent.parent.parent
UPLOAD_DIR = _ROOT / "sample_data" / "uploads"
HISTORY_FILE = UPLOAD_DIR / "upload_history.json"


def ensure_dirs() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def load() -> list[dict]:
    """Return all upload records, newest-first."""
    ensure_dirs()
    if not HISTORY_FILE.exists():
        return []
    try:
        data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save(records: list[dict]) -> None:
    ensure_dirs()
    HISTORY_FILE.write_text(
        json.dumps(records, indent=2, default=str),
        encoding="utf-8",
    )


def get_by_id(file_id: str) -> Optional[dict]:
    return next((r for r in load() if r.get("id") == file_id), None)


def upsert(record: dict) -> None:
    """Insert or replace a record (matched on ``id``). Prepends so newest is first."""
    with _LOCK:
        records = load()
        records = [r for r in records if r.get("id") != record["id"]]
        records.insert(0, record)
        save(records[:500])


def remove(file_id: str) -> bool:
    """Delete a record. Returns True if something was deleted."""
    with _LOCK:
        records = load()
        filtered = [r for r in records if r.get("id") != file_id]
        if len(filtered) == len(records):
            return False
        save(filtered)
        return True
