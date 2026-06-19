"""Processing router: POST /api/process-upload/{file_id}.

For SWIFT MT103 (.txt): runs the full AI pipeline — compliance, FX, liquidity,
risk, and decision engines — and returns a structured result.

If the decision is ESCALATE, a Maestro case is automatically created and
persisted to data/cases.json. The upload record is updated with linked_case_id.

For CSV / JSON: validates format, returns preview and record summary.
For PDF: acknowledges receipt and describes OCR integration point.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException

from src.web import history as hist, store

router = APIRouter()


@router.post("/process-upload/{file_id}")
def process_upload(file_id: str):
    """Run the OmniTreasury AI pipeline on a previously uploaded file."""
    record = hist.get_by_id(file_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Upload '{file_id}' not found.")

    saved_path = hist.UPLOAD_DIR / record.get("saved_as", "")
    if not saved_path.exists():
        raise HTTPException(
            status_code=404,
            detail="File not found on disk. It may have been deleted.",
        )

    ext  = record.get("extension", "")
    data = saved_path.read_bytes()

    if ext == ".txt":
        result = _run_swift_pipeline(data, record)
    elif ext == ".csv":
        result = _run_csv_preview(record)
    elif ext == ".json":
        result = _run_json_preview(data, record)
    elif ext == ".pdf":
        result = _run_pdf_placeholder(record)
    else:
        raise HTTPException(status_code=400, detail=f"No processor for '{ext}'.")

    status = "error" if result.get("error") else "processed"
    record["status"]            = status
    record["processing_result"] = result
    record["processing_error"]  = result.get("error")

    if result.get("case_id"):
        record["linked_case_id"] = result["case_id"]

    hist.upsert(record)

    # Emit audit event for pipeline completion
    if not result.get("error"):
        decision_val = (result.get("decision") or {}).get("decision", "")
        risk_val     = (result.get("risk") or {}).get("composite_score")
        store.add_audit(
            event_type="PIPELINE_COMPLETE",
            description=(
                f"Pipeline complete: {result.get('pipeline', ext)}"
                + (f" → {decision_val}" if decision_val else "")
                + (f" (risk {risk_val})" if risk_val is not None else "")
            ),
            upload_id=file_id,
            case_id=result.get("case_id"),
            details={"decision": decision_val, "risk_score": risk_val},
        )

    return {"success": status != "error", "file_id": file_id, "result": result}


# ── SWIFT MT103 full pipeline ──────────────────────────────────────────────────

def _run_swift_pipeline(data: bytes, record: dict) -> dict:
    try:
        from src.parsers.swift_mt103 import parse_mt103
        from src.engines.compliance_engine import ComplianceEngine
        from src.engines.forex_engine import ForexEngine
        from src.engines.liquidity_engine import LiquidityEngine
        from src.engines.risk_engine import RiskEngine
        from src.engines.decision_engine import DecisionEngine

        text       = data.decode("utf-8", errors="replace")
        payment    = parse_mt103(text)
        compliance = ComplianceEngine().run(payment)
        forex      = ForexEngine().run(payment)
        liquidity  = LiquidityEngine().run(payment)
        risk       = RiskEngine().run(payment)
        decision   = DecisionEngine().run(payment, compliance, forex, liquidity, risk)

        result: dict = {
            "pipeline": "SWIFT MT103",
            "payment": {
                "payment_id":       payment.payment_id,
                "amount":           float(payment.amount),
                "source_currency":  payment.source_currency,
                "target_currency":  payment.target_currency,
                "counterparty":     payment.counterparty.name,
                "bank_country":     payment.counterparty.bank_country,
                "purpose":          payment.purpose.value,
                "urgency":          payment.urgency.value,
                "value_date":       str(payment.value_date),
                "reference":        payment.reference,
            },
            "compliance": {
                "decision":           compliance.decision.value,
                "confidence":         round(compliance.confidence, 3),
                "sanctions_matches":  len(compliance.sanctions_matches),
                "aml_flags":          len(compliance.aml_flags),
                "jurisdiction_risks": [j.country for j in compliance.jurisdiction_risks],
                "summary":            compliance.summary,
                "policy_references":  compliance.policy_references,
            },
            "forex": {
                "recommended_provider":   forex.recommended_provider,
                "recommended_rate":       float(forex.recommended_rate),
                "estimated_savings_usd":  float(forex.estimated_savings_usd),
                "timing":                 forex.timing_recommendation.value,
                "currency_pair":          f"{payment.source_currency}/{payment.target_currency}",
            },
            "liquidity": {
                "status":               liquidity.status.value,
                "available_balance":    float(liquidity.source_position.available_balance),
                "post_payment_balance": float(liquidity.post_payment_balance),
                "covenant_at_risk":     liquidity.covenant_at_risk,
                "recommended_action":   liquidity.recommended_action,
                "netting_available":    liquidity.netting_opportunity is not None,
            },
            "risk": {
                "composite_score": round(risk.composite_score, 1),
                "risk_level":      risk.risk_level.value,
                "limit_breaches":  risk.limit_breaches,
                "factor_scores":   {f.category.value: round(f.score, 1) for f in risk.factors},
                "mitigations":     risk.mitigation_recommendations[:3],
            },
            "decision": {
                "decision":         decision.decision.value,
                "escalation_level": decision.escalation_level.value if decision.escalation_level else None,
                "execution_route":  decision.execution_route,
                "summary":          decision.summary,
                "confidence":       round(decision.confidence, 3),
            },
        }

        # ── Auto-create Maestro case on ESCALATE ──────────────────────────────
        if decision.decision.value == "ESCALATE":
            case_id       = f"CASE-{uuid.uuid4().hex[:8].upper()}"
            assigned_role = (
                decision.escalation_level.value
                if decision.escalation_level else "TREASURY_MANAGER"
            )
            priority = "HIGH" if float(payment.amount) >= 500_000 else "MEDIUM"
            sla_map  = {
                "CFO": 240, "TREASURY_MANAGER": 120,
                "COMPLIANCE_OFFICER": 60, "LEGAL": 480,
            }
            sla_mins = sla_map.get(assigned_role, 120)
            now_iso  = datetime.now(timezone.utc).isoformat()

            store.upsert_case({
                "case_id":        case_id,
                "upload_id":      record.get("id"),
                "payment_id":     payment.payment_id,
                "title":          (
                    f"{payment.payment_id} requires "
                    f"{assigned_role.replace('_', ' ')} review"
                ),
                "case_type":      "PAYMENT_ESCALATION",
                "priority":       priority,
                "assigned_role":  assigned_role,
                "status":         "OPEN",
                "risk_score":     round(risk.composite_score, 1),
                "amount":         float(payment.amount),
                "currency":       str(payment.source_currency),
                "counterparty":   payment.counterparty.name,
                "created_at":     now_iso,
                "updated_at":     now_iso,
                "closed_at":      None,
                "reviewer":       None,
                "reviewer_notes": None,
                "sla_minutes":    sla_mins,
                "payload": {
                    "decision_summary":      decision.summary,
                    "compliance_decision":   compliance.decision.value,
                    "fx_savings":            float(forex.estimated_savings_usd),
                    "liquidity_status":      liquidity.status.value,
                    "risk_level":            risk.risk_level.value,
                    "escalation_rationale":  [r.description for r in decision.rationales[:3]],
                },
            })
            store.add_audit(
                event_type="CASE_CREATED",
                description=(
                    f"Maestro case {case_id} created: {payment.payment_id} "
                    f"escalated to {assigned_role}"
                ),
                upload_id=record.get("id"),
                case_id=case_id,
                details={
                    "risk_score": round(risk.composite_score, 1),
                    "amount":     float(payment.amount),
                },
            )
            result["case_id"] = case_id

        return result

    except Exception as exc:
        return {
            "pipeline": "SWIFT MT103",
            "error":    str(exc),
            "hint":     "Ensure the file contains a valid SWIFT MT103 message with :20: and :32A: fields.",
        }


# ── CSV preview ────────────────────────────────────────────────────────────────

def _run_csv_preview(record: dict) -> dict:
    meta  = record.get("metadata", {})
    rows  = record.get("preview_rows", [])
    total = meta.get("total_amount")
    return {
        "pipeline":     "CSV Batch",
        "status":       "validated",
        "row_count":    meta.get("row_count", 0),
        "column_count": meta.get("column_count", 0),
        "columns":      meta.get("columns", []),
        "payment_ids":  meta.get("payment_ids", []),
        "total_amount": total,
        "preview":      rows,
        "message": (
            f"CSV validated. {meta.get('row_count', 0)} payment records found. "
            f"Total value: ${total:,.2f}." if total else
            f"CSV validated. {meta.get('row_count', 0)} rows found."
        ),
        "next_step": (
            "Call POST /api/process-batch with this file to run the full "
            "OmniTreasury pipeline on each payment record."
        ),
    }


# ── JSON preview ───────────────────────────────────────────────────────────────

def _run_json_preview(data: bytes, record: dict) -> dict:
    import json
    meta  = record.get("metadata", {})
    total = meta.get("total_amount")
    try:
        payload      = json.loads(data.decode("utf-8", errors="replace"))
        records_list = (
            payload if isinstance(payload, list)
            else payload.get("payments", payload.get("records", [payload]))
        )
        sample = records_list[:3] if isinstance(records_list, list) else []
    except Exception:
        sample = []

    return {
        "pipeline":       "JSON Payment",
        "status":         "validated",
        "record_count":   meta.get("record_count", 0),
        "payment_ids":    meta.get("payment_ids", []),
        "currencies":     meta.get("currencies", []),
        "total_amount":   total,
        "sample_records": sample,
        "message": (
            f"JSON validated. {meta.get('record_count', 0)} payment records extracted. "
            + (f"Total value: ${total:,.2f}." if total else "")
        ),
        "next_step": (
            "Each JSON payment record can be individually submitted to the "
            "OmniTreasury pipeline via POST /api/upload."
        ),
    }


# ── PDF placeholder ────────────────────────────────────────────────────────────

def _run_pdf_placeholder(record: dict) -> dict:
    meta = record.get("metadata", {})
    return {
        "pipeline":        "PDF Document",
        "status":          "received",
        "is_valid_pdf":    meta.get("is_valid_pdf", False),
        "estimated_pages": meta.get("estimated_pages"),
        "size_kb":         meta.get("size_kb"),
        "title":           meta.get("title", ""),
        "message":         "PDF document received and stored successfully.",
        "ocr_note": (
            "PDF text extraction is ready for integration with Azure Document "
            "Intelligence, AWS Textract, or a local pytesseract pipeline. "
            "Once extracted, the SWIFT/payment fields can be submitted to the "
            "OmniTreasury AI pipeline for full processing."
        ),
        "integration_points": [
            "Azure Document Intelligence (Form Recognizer)",
            "AWS Textract — detect payment table structures",
            "pytesseract — offline OCR for text-heavy PDFs",
            "PyMuPDF (fitz) — extract embedded text from digital PDFs",
        ],
    }
