"""Upload router: POST /api/upload, GET /api/uploads, DELETE /api/uploads/{id}."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from src.upload.file_processor import FileProcessor
from src.web import history as hist

router = APIRouter()

_processor = FileProcessor()
_ALLOWED = {".txt", ".csv", ".json", ".pdf"}


def fmtsize(b: int) -> str:
    if b < 1024:
        return f"{b} B"
    if b < 1_048_576:
        return f"{b/1024:.1f} KB"
    return f"{b/1_048_576:.1f} MB"


# ── Health ─────────────────────────────────────────────────────────────────────

@router.get("/health")
def health():
    from datetime import datetime, timezone
    records = hist.load()
    processed = sum(1 for r in records if r.get("status") == "processed")
    return {
        "status": "ok",
        "version": "1.0.0",
        "service": "OmniTreasury AI",
        "upload_dir": str(hist.UPLOAD_DIR),
        "total_uploads": len(records),
        "processed": processed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Uploads list ───────────────────────────────────────────────────────────────

@router.get("/uploads")
def list_uploads():
    """Return all upload records, newest first."""
    return hist.load()


@router.get("/uploads/{file_id}")
def get_upload(file_id: str):
    record = hist.get_by_id(file_id)
    if not record:
        raise HTTPException(status_code=404, detail="Upload not found")
    return record


@router.delete("/uploads/{file_id}")
def delete_upload(file_id: str):
    record = hist.get_by_id(file_id)
    if not record:
        raise HTTPException(status_code=404, detail="Upload not found")

    # Remove file from disk if present
    target = hist.UPLOAD_DIR / record.get("saved_as", "")
    if target.exists():
        target.unlink()

    if not hist.remove(file_id):
        raise HTTPException(status_code=404, detail="Upload not found")

    return {"success": True, "deleted": file_id}


# ── Upload ─────────────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Accept a file, validate, save to disk, and return the upload record."""
    hist.ensure_dirs()

    filename = file.filename or "upload.bin"
    ext = Path(filename).suffix.lower()

    if ext not in _ALLOWED:
        raise HTTPException(
            status_code=422,
            detail=f"File type '{ext}' not supported. Allowed: {', '.join(sorted(_ALLOWED))}",
        )

    data = await file.read()

    if not data:
        raise HTTPException(status_code=422, detail="File is empty.")

    if len(data) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds 50 MB limit.")

    # Validate and extract metadata via existing FileProcessor
    processed = _processor.process(filename, data, uploaded_by="web-dashboard")

    if processed.status == "error":
        raise HTTPException(status_code=422, detail="; ".join(processed.errors))

    # Save raw bytes
    dest = hist.UPLOAD_DIR / processed.saved_name
    dest.write_bytes(data)

    record: dict = {
        "id": processed.upload_id,
        "filename": filename,
        "saved_as": processed.saved_name,
        "file_type": processed.file_type,
        "extension": ext,
        "size_bytes": len(data),
        "uploaded_at": processed.uploaded_at,
        "status": "uploaded",
        "metadata": processed.metadata,
        "preview_rows": processed.preview_rows[:5],
        "processing_result": None,
        "processing_error": None,
        "warnings": processed.errors,  # warnings from validation
    }

    hist.upsert(record)

    # Emit audit event
    from src.web import store
    store.add_audit(
        event_type="FILE_UPLOADED",
        description=f"File uploaded: {filename} ({fmtsize(len(data))})",
        upload_id=processed.upload_id,
        details={"filename": filename, "size_bytes": len(data), "file_type": processed.file_type},
    )

    return {"success": True, "file": record}
