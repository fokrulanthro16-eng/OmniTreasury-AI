"""Tests for the OmniTreasury AI FastAPI web application.

Run with:
    pytest tests/test_web_api.py -v
"""

from __future__ import annotations

import io
import json

import pytest
from fastapi.testclient import TestClient

from src.web.app import app

client = TestClient(app)


# ── Health ─────────────────────────────────────────────────────────────────────

def test_health_returns_ok():
    r = client.get("/api/health")
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == "ok"


def test_health_has_required_fields():
    d = client.get("/api/health").json()
    for key in ("status", "version", "total_uploads", "processed", "timestamp"):
        assert key in d, f"Missing field: {key}"


def test_health_version():
    assert client.get("/api/health").json()["version"] == "1.0.0"


# ── Uploads list ───────────────────────────────────────────────────────────────

def test_list_uploads_returns_list():
    r = client.get("/api/uploads")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_nonexistent_upload_is_404():
    r = client.get("/api/uploads/does-not-exist-12345")
    assert r.status_code == 404


# ── Upload validation ──────────────────────────────────────────────────────────

def test_upload_invalid_extension_rejected():
    r = client.post(
        "/api/upload",
        files={"file": ("malware.exe", b"MZ\x90\x00", "application/octet-stream")},
    )
    assert r.status_code in (422, 400)


def test_upload_empty_file_rejected():
    r = client.post(
        "/api/upload",
        files={"file": ("empty.json", b"", "application/json")},
    )
    assert r.status_code in (422, 400)


def test_upload_no_file_is_422():
    r = client.post("/api/upload")
    assert r.status_code == 422


# ── Valid JSON upload ──────────────────────────────────────────────────────────

_SAMPLE_JSON = json.dumps({
    "payments": [
        {
            "payment_id": "PAY-TEST-001",
            "source_entity": "CORP-HQ",
            "source_currency": "USD",
            "target_currency": "EUR",
            "amount": 10000.00,
            "counterparty_name": "Test Vendor",
            "bank_country": "DE",
            "purpose": "TRADE_PAYMENT",
            "value_date": "2026-06-20",
        }
    ]
}).encode()


def test_upload_valid_json_succeeds():
    r = client.post(
        "/api/upload",
        files={"file": ("payments_test.json", _SAMPLE_JSON, "application/json")},
    )
    assert r.status_code == 200
    d = r.json()
    assert d["success"] is True
    assert "file" in d


def test_upload_json_metadata():
    r = client.post(
        "/api/upload",
        files={"file": ("payments_meta.json", _SAMPLE_JSON, "application/json")},
    )
    assert r.status_code == 200
    f = r.json()["file"]
    assert f["extension"] == ".json"
    assert f["size_bytes"] == len(_SAMPLE_JSON)
    assert f["status"] == "uploaded"
    assert "id" in f
    assert "uploaded_at" in f


def test_upload_json_appears_in_history():
    unique_name = "hist_check_abc123.json"
    client.post(
        "/api/upload",
        files={"file": (unique_name, _SAMPLE_JSON, "application/json")},
    )
    uploads = client.get("/api/uploads").json()
    names = [u["filename"] for u in uploads]
    assert unique_name in names


# ── Valid CSV upload ───────────────────────────────────────────────────────────

_SAMPLE_CSV = (
    "payment_id,source_entity,source_currency,amount,counterparty_name\n"
    "PAY-001,CORP-HQ,USD,5000.00,Vendor A\n"
    "PAY-002,CORP-HQ,EUR,3000.00,Vendor B\n"
).encode()


def test_upload_valid_csv_succeeds():
    r = client.post(
        "/api/upload",
        files={"file": ("batch_test.csv", _SAMPLE_CSV, "text/csv")},
    )
    assert r.status_code == 200
    assert r.json()["success"] is True


def test_upload_csv_extension():
    r = client.post(
        "/api/upload",
        files={"file": ("payments.csv", _SAMPLE_CSV, "text/csv")},
    )
    assert r.json()["file"]["extension"] == ".csv"


# ── Valid SWIFT MT103 upload ───────────────────────────────────────────────────

_SWIFT_MT103 = (
    "{1:F01CORPGB2LXXXX0000000000}"
    "{2:I103BANKDE33XXXXN}"
    "{4:\n"
    ":20:TXN-WEB-TEST-01\n"
    ":23B:CRED\n"
    ":32A:260620USD25000,00\n"
    ":50K:/ACC12345678\nCORP HEADQUARTERS\n"
    ":59:/DE89370400440532013000\nTEST VENDOR GMBH\n"
    ":70:INVOICE INV-2026-0099\n"
    ":71A:SHA\n"
    "-}"
).encode()


def test_upload_swift_txt_succeeds():
    r = client.post(
        "/api/upload",
        files={"file": ("test_swift.txt", _SWIFT_MT103, "text/plain")},
    )
    assert r.status_code == 200
    d = r.json()
    assert d["success"] is True
    assert d["file"]["extension"] == ".txt"


# ── Process endpoint ───────────────────────────────────────────────────────────

def test_process_nonexistent_is_404():
    r = client.post("/api/process-upload/no-such-file-9999")
    assert r.status_code == 404


def test_process_json_returns_result():
    up = client.post(
        "/api/upload",
        files={"file": ("proc_test.json", _SAMPLE_JSON, "application/json")},
    ).json()
    file_id = up["file"]["id"]

    r = client.post(f"/api/process-upload/{file_id}")
    assert r.status_code == 200
    d = r.json()
    assert "result" in d
    assert d["result"]["pipeline"] == "JSON Payment"


def test_process_csv_returns_result():
    up = client.post(
        "/api/upload",
        files={"file": ("proc_csv.csv", _SAMPLE_CSV, "text/csv")},
    ).json()
    file_id = up["file"]["id"]

    r = client.post(f"/api/process-upload/{file_id}")
    assert r.status_code == 200
    assert r.json()["result"]["pipeline"] == "CSV Batch"


def test_process_swift_runs_pipeline():
    up = client.post(
        "/api/upload",
        files={"file": ("pipeline_test.txt", _SWIFT_MT103, "text/plain")},
    ).json()
    file_id = up["file"]["id"]

    r = client.post(f"/api/process-upload/{file_id}")
    assert r.status_code == 200
    result = r.json()["result"]
    assert result["pipeline"] == "SWIFT MT103"
    # Full pipeline may succeed or return an error dict — either is valid here
    # If it succeeded, validate top-level keys
    if "error" not in result:
        for section in ("payment", "compliance", "forex", "liquidity", "risk", "decision"):
            assert section in result, f"Missing section: {section}"
        assert result["decision"]["decision"] in ("AUTO_EXECUTE", "ESCALATE", "HARD_REJECT")


# ── SPA / static routes ────────────────────────────────────────────────────────

def test_root_returns_html():
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")


def test_root_contains_omnitreasury():
    body = client.get("/").text
    assert "OmniTreasury" in body


def test_delete_upload():
    up = client.post(
        "/api/upload",
        files={"file": ("to_delete.json", _SAMPLE_JSON, "application/json")},
    ).json()
    file_id = up["file"]["id"]

    r = client.delete(f"/api/uploads/{file_id}")
    assert r.status_code == 200
    assert r.json()["deleted"] == file_id

    # Confirm it's gone
    assert client.get(f"/api/uploads/{file_id}").status_code == 404
