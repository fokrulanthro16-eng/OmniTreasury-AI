"""File type detection, validation, and metadata extraction for uploaded documents.

Supports SWIFT MT103 (.txt), CSV payment batches (.csv),
JSON payment files (.json), and PDF documents (.pdf).
No third-party dependencies — stdlib only.
"""

from __future__ import annotations

import csv
import io
import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

ALLOWED_EXTENSIONS = {".txt", ".csv", ".json", ".pdf"}
MAX_FILE_BYTES = 50 * 1024 * 1024  # 50 MB

# Map extension → display label
FILE_TYPE_LABELS: dict[str, str] = {
    ".txt": "SWIFT MT103",
    ".csv": "CSV Batch",
    ".json": "JSON Payment",
    ".pdf": "PDF Document",
}


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class UploadedFile:
    upload_id: str
    original_name: str
    saved_name: str
    file_type: str          # e.g. "SWIFT MT103"
    extension: str          # e.g. ".txt"
    size_bytes: int
    uploaded_at: str        # ISO-8601 UTC string
    uploaded_by: str
    status: str             # "processed" | "error" | "pending"
    metadata: dict[str, Any] = field(default_factory=dict)
    preview_rows: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "upload_id": self.upload_id,
            "original_name": self.original_name,
            "saved_name": self.saved_name,
            "file_type": self.file_type,
            "extension": self.extension,
            "size_bytes": self.size_bytes,
            "uploaded_at": self.uploaded_at,
            "uploaded_by": self.uploaded_by,
            "status": self.status,
            "metadata": self.metadata,
            "preview_rows": self.preview_rows,
            "errors": self.errors,
        }


class FileProcessor:
    """Validates and extracts metadata from uploaded files."""

    def validate(self, filename: str, data: bytes) -> ValidationResult:
        """Return ValidationResult with any errors or warnings."""
        errors: list[str] = []
        warnings: list[str] = []

        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            errors.append(
                f"File type '{ext}' is not supported. "
                f"Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
            return ValidationResult(valid=False, errors=errors)

        if len(data) == 0:
            errors.append("File is empty.")
            return ValidationResult(valid=False, errors=errors)

        if len(data) > MAX_FILE_BYTES:
            errors.append(
                f"File size {len(data) / 1_048_576:.1f} MB exceeds 50 MB limit."
            )
            return ValidationResult(valid=False, errors=errors)

        # Type-specific validation
        if ext == ".json":
            try:
                json.loads(data.decode("utf-8", errors="replace"))
            except json.JSONDecodeError as exc:
                errors.append(f"Invalid JSON: {exc}")
        elif ext == ".csv":
            try:
                text = data.decode("utf-8", errors="replace")
                reader = csv.reader(io.StringIO(text))
                rows = list(reader)
                if len(rows) < 2:
                    warnings.append("CSV appears to have no data rows (only header or empty).")
            except Exception as exc:
                errors.append(f"CSV parse error: {exc}")
        elif ext == ".txt":
            text = data.decode("utf-8", errors="replace")
            if not any(tag in text for tag in (":20:", ":32A:", "{4:", "MT103")):
                warnings.append(
                    "File does not appear to be a standard SWIFT MT103 message "
                    "(no :20:, :32A:, or {4: block found). "
                    "Proceeding with raw text storage."
                )

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def process(
        self,
        filename: str,
        data: bytes,
        uploaded_by: str = "dashboard@nexusglobal.com",
    ) -> UploadedFile:
        """Validate file, extract metadata, and return an UploadedFile record."""
        ext = Path(filename).suffix.lower()
        upload_id = str(uuid.uuid4())[:8].upper()
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        saved_name = f"{now[:10].replace('-','')}_{upload_id}_{Path(filename).name}"
        file_type = FILE_TYPE_LABELS.get(ext, "Unknown")

        validation = self.validate(filename, data)
        status = "processed" if validation.valid else "error"

        metadata: dict[str, Any] = {}
        preview_rows: list[dict] = []

        if validation.valid:
            if ext == ".txt":
                metadata, preview_rows = self._parse_swift(data)
            elif ext == ".csv":
                metadata, preview_rows = self._parse_csv(data)
            elif ext == ".json":
                metadata, preview_rows = self._parse_json(data)
            elif ext == ".pdf":
                metadata = self._parse_pdf_meta(filename, data)

        return UploadedFile(
            upload_id=upload_id,
            original_name=filename,
            saved_name=saved_name,
            file_type=file_type,
            extension=ext,
            size_bytes=len(data),
            uploaded_at=now,
            uploaded_by=uploaded_by,
            status=status,
            metadata=metadata,
            preview_rows=preview_rows,
            errors=validation.errors + validation.warnings,
        )

    # ── Type-specific parsers ─────────────────────────────────────────────────

    def _parse_swift(self, data: bytes) -> tuple[dict, list[dict]]:
        text = data.decode("utf-8", errors="replace")
        fields: dict[str, str] = {}

        # Extract block 4 content if present
        block4_match = re.search(r"\{4:(.*?)-\}", text, re.DOTALL)
        body = block4_match.group(1).strip() if block4_match else text

        # Parse :TAG: VALUE pairs
        for m in re.finditer(r":(\w+):(.*?)(?=:\w+:|$)", body, re.DOTALL):
            fields[m.group(1)] = m.group(2).strip()

        # Field :32A: = YYMMDDCURRENCYAMOUNT  e.g. 260617USD50000,00
        currency, amount, value_date = "", "", ""
        if "32A" in fields:
            raw = fields["32A"]
            date_match = re.match(r"(\d{6})", raw)
            curr_match = re.search(r"([A-Z]{3})", raw)
            amt_match = re.search(r"[A-Z]{3}([\d,]+)", raw)
            if date_match:
                d = date_match.group(1)
                value_date = f"20{d[:2]}-{d[2:4]}-{d[4:]}"
            if curr_match:
                currency = curr_match.group(1)
            if amt_match:
                amount = amt_match.group(1).replace(",", ".")

        metadata = {
            "transaction_ref": fields.get("20", ""),
            "bank_operation": fields.get("23B", "CRED"),
            "currency": currency,
            "amount": amount,
            "value_date": value_date,
            "ordering_customer": fields.get("50K", fields.get("50A", ""))[:80],
            "beneficiary": fields.get("59", "")[:80],
            "remittance_info": fields.get("70", "")[:120],
            "charges": fields.get("71A", ""),
            "field_count": len(fields),
        }
        preview_rows = [{"Field": k, "Value": v[:80]} for k, v in list(fields.items())[:8]]
        return metadata, preview_rows

    def _parse_csv(self, data: bytes) -> tuple[dict, list[dict]]:
        text = data.decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        headers = reader.fieldnames or []
        preview_rows = [dict(r) for r in rows[:5]]

        # Try to detect payment_id column
        id_col = next(
            (c for c in headers if "payment_id" in c.lower() or "id" in c.lower()),
            None,
        )
        ids = [r[id_col] for r in rows if id_col and r.get(id_col)] if id_col else []

        # Try to detect amount column
        amt_col = next(
            (c for c in headers if "amount" in c.lower() or "value" in c.lower()),
            None,
        )
        amounts = []
        if amt_col:
            for r in rows:
                try:
                    amounts.append(float(r.get(amt_col, "0").replace(",", "")))
                except ValueError:
                    pass

        metadata = {
            "row_count": len(rows),
            "column_count": len(headers),
            "columns": list(headers),
            "payment_ids": ids[:10],
            "total_amount": round(sum(amounts), 2) if amounts else None,
            "id_column": id_col,
            "amount_column": amt_col,
        }
        return metadata, preview_rows

    def _parse_json(self, data: bytes) -> tuple[dict, list[dict]]:
        payload = json.loads(data.decode("utf-8", errors="replace"))
        records: list[dict] = []

        if isinstance(payload, list):
            records = payload
        elif isinstance(payload, dict):
            # Try common wrapper keys
            for key in ("payments", "records", "data", "transactions"):
                if isinstance(payload.get(key), list):
                    records = payload[key]
                    break
            if not records:
                records = [payload]  # single payment object

        ids = [r.get("payment_id", r.get("id", "")) for r in records if isinstance(r, dict)]
        currencies = list({r.get("source_currency", "") for r in records if isinstance(r, dict)})
        amounts = []
        for r in records:
            if isinstance(r, dict):
                try:
                    amounts.append(float(r.get("amount", 0)))
                except (TypeError, ValueError):
                    pass

        metadata = {
            "record_count": len(records),
            "payment_ids": [i for i in ids if i][:10],
            "currencies": [c for c in currencies if c],
            "total_amount": round(sum(amounts), 2) if amounts else None,
            "top_level_keys": list(payload.keys()) if isinstance(payload, dict) else [],
        }
        preview_rows = [r for r in records[:5] if isinstance(r, dict)]
        return metadata, preview_rows

    def _parse_pdf_meta(self, filename: str, data: bytes) -> dict:
        """Extract what we can from a PDF without external libraries."""
        # Scan for PDF metadata strings in the binary
        text_fragment = data[:4096].decode("latin-1", errors="replace")
        title_match = re.search(r"/Title\s*\(([^)]+)\)", text_fragment)
        author_match = re.search(r"/Author\s*\(([^)]+)\)", text_fragment)
        pages_match = re.search(r"/N\s+(\d+)", text_fragment)
        is_pdf = data[:4] == b"%PDF"
        return {
            "is_valid_pdf": is_pdf,
            "title": title_match.group(1) if title_match else "",
            "author": author_match.group(1) if author_match else "",
            "estimated_pages": int(pages_match.group(1)) if pages_match else None,
            "size_kb": round(len(data) / 1024, 1),
        }
