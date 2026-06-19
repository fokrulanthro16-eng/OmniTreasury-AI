"""Lightweight upload HTTP server for OmniTreasury AI.

Runs on http://127.0.0.1:8765 — no external dependencies.
The dashboard fetches this endpoint via JS fetch() with CORS.

Routes
------
GET  /health          → {"status": "ok"}
GET  /uploads         → JSON list of all uploaded files
POST /upload          → multipart/form-data file upload
DELETE /upload/{name} → delete a file from uploads/

Usage
-----
    python -m src.upload.upload_server          # start server
    python -m src.upload.upload_server --port 8765

Or from demo.py / main.py integration:
    from src.upload.upload_server import run_upload_server
    run_upload_server()   # blocks; call in a thread for background use
"""

from __future__ import annotations

import io
import json
import os
import re
import shutil
import sys
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from src.upload.file_processor import FileProcessor

# ── Paths ──────────────────────────────────────────────────────────────────────
_ROOT = Path(__file__).parent.parent.parent
UPLOAD_DIR = _ROOT / "sample_data" / "uploads"
REGISTRY_PATH = UPLOAD_DIR / "registry.json"

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765

_processor = FileProcessor()
_registry_lock = threading.Lock()


# ── Registry helpers ───────────────────────────────────────────────────────────

def _ensure_upload_dir() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _load_registry() -> list[dict]:
    _ensure_upload_dir()
    if not REGISTRY_PATH.exists():
        return []
    try:
        with open(REGISTRY_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_registry(records: list[dict]) -> None:
    _ensure_upload_dir()
    with open(REGISTRY_PATH, "w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2, default=str)


def _append_to_registry(record: dict) -> None:
    with _registry_lock:
        records = _load_registry()
        records.insert(0, record)          # newest first
        records = records[:200]             # cap at 200 entries
        _save_registry(records)


# ── Multipart parser (no deprecated cgi module) ────────────────────────────────

def _parse_boundary(content_type: str) -> str | None:
    m = re.search(r"boundary=([^\s;]+)", content_type)
    return m.group(1).strip('"') if m else None


def _parse_multipart(body: bytes, boundary: str) -> list[dict[str, Any]]:
    """Split multipart/form-data body into parts. Returns list of dicts."""
    sep = ("--" + boundary).encode()
    parts: list[dict[str, Any]] = []

    for section in body.split(sep)[1:]:           # skip preamble
        if section.strip() in (b"--", b"--\r\n", b"--\n"):
            break
        # Split headers / body at the first blank line
        if b"\r\n\r\n" in section:
            raw_headers, content = section.split(b"\r\n\r\n", 1)
        elif b"\n\n" in section:
            raw_headers, content = section.split(b"\n\n", 1)
        else:
            continue

        content = content.rstrip(b"\r\n")

        # Parse header lines
        headers: dict[str, str] = {}
        for line in raw_headers.split(b"\r\n"):
            if b":" in line:
                k, v = line.split(b":", 1)
                headers[k.strip().lower().decode("latin-1")] = v.strip().decode("latin-1")

        disposition = headers.get("content-disposition", "")
        name_m = re.search(r'name="([^"]+)"', disposition)
        file_m = re.search(r'filename="([^"]*)"', disposition)
        parts.append({
            "name": name_m.group(1) if name_m else "",
            "filename": file_m.group(1) if file_m else None,
            "content_type": headers.get("content-type", "application/octet-stream"),
            "data": content,
        })

    return parts


# ── HTTP handler ───────────────────────────────────────────────────────────────

class _UploadHandler(BaseHTTPRequestHandler):
    """Handle upload requests from the dashboard."""

    server_version = "OmniTreasury-Upload/1.0"
    protocol_version = "HTTP/1.1"

    # Silence the default request logging (we use our own)
    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: ANN401
        pass

    # ── CORS preflight ─────────────────────────────────────────────────────────

    def do_OPTIONS(self) -> None:                        # noqa: N802
        self.send_response(200)
        self._add_cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    # ── GET ────────────────────────────────────────────────────────────────────

    def do_GET(self) -> None:                            # noqa: N802
        path = self.path.split("?")[0]

        if path == "/health":
            self._json(200, {
                "status": "ok",
                "version": "1.0",
                "upload_dir": str(UPLOAD_DIR),
                "total_uploads": len(_load_registry()),
            })

        elif path == "/uploads":
            self._json(200, _load_registry())

        else:
            self._json(404, {"error": "Not found"})

    # ── POST ───────────────────────────────────────────────────────────────────

    def do_POST(self) -> None:                           # noqa: N802
        if self.path.split("?")[0] != "/upload":
            self._json(404, {"error": "Not found"})
            return

        content_type = self.headers.get("Content-Type", "")
        content_length = int(self.headers.get("Content-Length", 0))

        if content_length > 50 * 1024 * 1024:
            self._json(413, {"error": "File too large (50 MB limit)"})
            return

        body = self.rfile.read(content_length)
        boundary = _parse_boundary(content_type)

        if not boundary:
            self._json(400, {"error": "Missing multipart boundary"})
            return

        parts = _parse_multipart(body, boundary)
        file_part = next((p for p in parts if p.get("filename")), None)

        if not file_part:
            self._json(400, {"error": "No file found in request"})
            return

        filename = file_part["filename"] or "upload.bin"
        data: bytes = file_part["data"]

        # Extract optional uploader field
        uploader_part = next((p for p in parts if p.get("name") == "uploaded_by"), None)
        uploaded_by = (
            uploader_part["data"].decode("utf-8", errors="replace").strip()
            if uploader_part
            else "dashboard@nexusglobal.com"
        )

        # Process the file
        result = _processor.process(filename, data, uploaded_by=uploaded_by)

        if result.status == "error":
            self._json(422, {
                "success": False,
                "errors": result.errors,
                "file": result.original_name,
            })
            return

        # Save the file to disk
        _ensure_upload_dir()
        dest = UPLOAD_DIR / result.saved_name
        dest.write_bytes(data)

        # Append to registry
        record = result.to_dict()
        _append_to_registry(record)

        print(
            f"  [UPLOAD] {filename} → {result.saved_name} "
            f"({len(data)} bytes, {result.file_type})"
        )

        self._json(200, {"success": True, "file": record})

    # ── DELETE ─────────────────────────────────────────────────────────────────

    def do_DELETE(self) -> None:                         # noqa: N802
        # Expect DELETE /upload/{saved_name}
        m = re.match(r"^/upload/(.+)$", self.path)
        if not m:
            self._json(404, {"error": "Not found"})
            return

        saved_name = m.group(1)
        # Safety: no path traversal
        if "/" in saved_name or "\\" in saved_name or ".." in saved_name:
            self._json(400, {"error": "Invalid filename"})
            return

        target = UPLOAD_DIR / saved_name
        if not target.exists():
            self._json(404, {"error": "File not found"})
            return

        target.unlink()

        # Remove from registry
        with _registry_lock:
            records = [r for r in _load_registry() if r.get("saved_name") != saved_name]
            _save_registry(records)

        self._json(200, {"success": True, "deleted": saved_name})

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _add_cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Requested-With")

    def _json(self, code: int, payload: Any) -> None:    # noqa: ANN401
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(code)
        self._add_cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


# ── Public API ─────────────────────────────────────────────────────────────────

class UploadServer:
    """Wrapper around HTTPServer for use in threading contexts."""

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
        self.host = host
        self.port = port
        self._server: HTTPServer | None = None

    def start(self, daemon: bool = True) -> None:
        """Start server in a background daemon thread."""
        _ensure_upload_dir()
        self._server = HTTPServer((self.host, self.port), _UploadHandler)
        t = threading.Thread(target=self._server.serve_forever, daemon=daemon)
        t.start()
        print(f"  [UPLOAD SERVER] Listening on http://{self.host}:{self.port}")

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


def run_upload_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> None:
    """Block and serve upload requests until Ctrl-C."""
    _ensure_upload_dir()
    print(f"\n  OmniTreasury Upload Server")
    print(f"  ──────────────────────────")
    print(f"  Listening : http://{host}:{port}")
    print(f"  Upload dir: {UPLOAD_DIR}")
    print(f"  Press Ctrl-C to stop\n")

    server = HTTPServer((host, port), _UploadHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  [UPLOAD SERVER] Stopped.")
        server.shutdown()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    run_upload_server(port=port)
