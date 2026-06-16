"""Reset OmniTreasury AI to a clean, judge-ready demo state.

Usage:
    python scripts/reset_demo_data.py

What it does:
  1. Rewrites sample_data/uploads/upload_history.json with 3 canonical demo uploads
  2. Creates data/cases.json with one OPEN escalation case (£2.1M GBP acquisition)
  3. Creates data/audit.json with 5 seed audit events

Run this before every demo session to ensure a consistent starting state.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).parent.parent
UPLOAD_HISTORY = _ROOT / "sample_data" / "uploads" / "upload_history.json"
CASES_FILE     = _ROOT / "data" / "cases.json"
AUDIT_FILE     = _ROOT / "data" / "audit.json"


# ── Demo upload records ────────────────────────────────────────────────────────

DEMO_UPLOADS = [
    {
        "id": "DEMO0003",
        "filename": "treasury_payments_q2_demo.json",
        "saved_as": "treasury_payments_q2_demo.json",
        "file_type": "JSON Payment",
        "extension": ".json",
        "size_bytes": 2050,
        "uploaded_at": "2026-06-15T08:40:00Z",
        "status": "processed",
        "linked_case_id": "CASE-DEMO-001",
        "metadata": {
            "record_count": 4,
            "payment_ids": ["PAY-Q2-001", "PAY-Q2-002", "PAY-Q2-003", "PAY-Q2-004"],
            "currencies": ["EUR", "GBP", "SGD", "USD"],
            "total_amount": 2995000.0,
        },
        "preview_rows": [
            {
                "payment_id": "PAY-Q2-001",
                "source_currency": "EUR",
                "amount": 95000.0,
                "counterparty_name": "Alpine Precision Engineering GmbH",
                "purpose": "TRADE_PAYMENT",
            },
            {
                "payment_id": "PAY-Q2-002",
                "source_currency": "GBP",
                "amount": 2100000.0,
                "counterparty_name": "Manchester Industrial Holdings PLC",
                "purpose": "ACQUISITION",
            },
        ],
        "processing_result": {
            "pipeline": "JSON Payment",
            "status": "validated",
            "record_count": 4,
            "payment_ids": ["PAY-Q2-001", "PAY-Q2-002", "PAY-Q2-003", "PAY-Q2-004"],
            "currencies": ["EUR", "GBP", "SGD", "USD"],
            "total_amount": 2995000.0,
            "sample_records": [
                {
                    "payment_id": "PAY-Q2-001",
                    "scenario": "CLEAN_PAYMENT",
                    "source_entity": "CORP-HQ",
                    "source_currency": "EUR",
                    "amount": 95000.0,
                    "target_currency": "USD",
                    "counterparty": {
                        "name": "Alpine Precision Engineering GmbH",
                        "bank_country": "CH",
                        "bank_swift_code": "UBSWCHZH",
                    },
                    "value_date": "2026-06-20",
                    "purpose": "TRADE_PAYMENT",
                    "urgency": "T_PLUS_2",
                },
                {
                    "payment_id": "PAY-Q2-002",
                    "scenario": "HIGH_VALUE_CFO",
                    "source_entity": "CORP-EMEA",
                    "source_currency": "GBP",
                    "amount": 2100000.0,
                    "target_currency": "USD",
                    "counterparty": {
                        "name": "Manchester Industrial Holdings PLC",
                        "bank_country": "GB",
                        "bank_swift_code": "NWBKGB2L",
                    },
                    "value_date": "2026-06-21",
                    "purpose": "ACQUISITION",
                    "urgency": "FLEXIBLE",
                },
                {
                    "payment_id": "PAY-Q2-003",
                    "scenario": "INTERCOMPANY",
                    "source_entity": "CORP-APAC",
                    "source_currency": "SGD",
                    "amount": 480000.0,
                    "target_currency": "USD",
                    "counterparty": {
                        "name": "Nexus Global Corporation",
                        "bank_country": "US",
                        "bank_swift_code": "CHASUS33",
                    },
                    "value_date": "2026-06-18",
                    "purpose": "DIVIDEND",
                    "urgency": "T_PLUS_2",
                },
            ],
            "message": "JSON validated. 4 payment records extracted. Total value: $2,995,000.00.",
            "next_step": "Each JSON payment record can be individually submitted to the OmniTreasury pipeline via POST /api/upload.",
        },
        "processing_error": None,
        "warnings": [],
    },
    {
        "id": "DEMO0002",
        "filename": "batch_payments_june_demo.csv",
        "saved_as": "batch_payments_june_demo.csv",
        "file_type": "CSV Batch",
        "extension": ".csv",
        "size_bytes": 1131,
        "uploaded_at": "2026-06-15T08:35:00Z",
        "status": "processed",
        "metadata": {
            "row_count": 8,
            "column_count": 11,
            "columns": [
                "payment_id", "source_entity", "source_currency", "amount",
                "target_currency", "counterparty_name", "bank_country",
                "value_date", "purpose", "urgency", "submitted_by",
            ],
            "payment_ids": [
                "PAY-BATCH-001", "PAY-BATCH-002", "PAY-BATCH-003", "PAY-BATCH-004",
                "PAY-BATCH-005", "PAY-BATCH-006", "PAY-BATCH-007", "PAY-BATCH-008",
            ],
            "total_amount": 1495500.0,
        },
        "preview_rows": [
            {
                "payment_id": "PAY-BATCH-001",
                "source_entity": "CORP-HQ",
                "source_currency": "EUR",
                "amount": "75000.00",
                "target_currency": "USD",
                "counterparty_name": "Acme Supplies GmbH",
                "bank_country": "DE",
                "value_date": "2026-06-18",
                "purpose": "TRADE_PAYMENT",
                "urgency": "T_PLUS_2",
                "submitted_by": "treasury@nexusglobal.com",
            },
            {
                "payment_id": "PAY-BATCH-002",
                "source_entity": "CORP-EMEA",
                "source_currency": "GBP",
                "amount": "120000.00",
                "target_currency": "USD",
                "counterparty_name": "London Tech Partners Ltd",
                "bank_country": "GB",
                "value_date": "2026-06-18",
                "purpose": "SERVICES",
                "urgency": "T_PLUS_2",
                "submitted_by": "emea.ops@nexusglobal.com",
            },
        ],
        "processing_result": {
            "pipeline": "CSV Batch",
            "status": "validated",
            "row_count": 8,
            "column_count": 11,
            "total_amount": 1495500.0,
            "message": "CSV validated. 8 payment records found. Total value: $1,495,500.00.",
            "next_step": "Call POST /api/process-batch with this file to run the full OmniTreasury pipeline on each payment record.",
        },
        "processing_error": None,
        "warnings": [],
    },
    {
        "id": "DEMO0001",
        "filename": "sample_swift_mt103_demo.txt",
        "saved_as": "sample_swift_mt103_demo.txt",
        "file_type": "SWIFT MT103",
        "extension": ".txt",
        "size_bytes": 410,
        "uploaded_at": "2026-06-15T08:30:00Z",
        "status": "processed",
        "metadata": {
            "transaction_ref": "TXN-2026-DEMO-001",
            "bank_operation": "CRED",
            "currency": "USD",
            "amount": "50000.00",
            "value_date": "2026-06-17",
            "ordering_customer": "/DE89370400440532013000\nNEXUS GLOBAL CORPORATION\nFRANKFURT AM MAIN\nGERMANY",
            "beneficiary": "/US0900040012345678\nACME MANUFACTURING INC\nNEW YORK NY 10001\nUNITED STATES",
            "remittance_info": "INV-2026-ACM-DEMO-001 TRADE PAYMENT Q2 2026",
            "charges": "SHA",
            "field_count": 10,
        },
        "preview_rows": [
            {"Field": "20", "Value": "TXN-2026-DEMO-001"},
            {"Field": "23B", "Value": "CRED"},
            {"Field": "32A", "Value": "260617USD50000,00"},
            {"Field": "50K", "Value": "/DE89370400440532013000\nNEXUS GLOBAL CORPORATION"},
            {"Field": "59", "Value": "/US0900040012345678\nACME MANUFACTURING INC"},
        ],
        "processing_result": {
            "pipeline": "SWIFT MT103",
            "payment": {
                "payment_id": "PAY-E01C18C5",
                "amount": 50000.0,
                "source_currency": "USD",
                "target_currency": "USD",
                "counterparty": "ACME MANUFACTURING INC",
                "bank_country": "US",
                "purpose": "TRADE_PAYMENT",
                "urgency": "T_PLUS_2",
                "value_date": "2026-06-17",
                "reference": "TXN-2026-DEMO-001",
            },
            "compliance": {
                "decision": "CLEAR",
                "confidence": 0.97,
                "sanctions_matches": 0,
                "aml_flags": 2,
                "jurisdiction_risks": [],
                "summary": "Decision: CLEAR. AML: 2 pattern flag(s) detected.",
                "policy_references": ["Bank Secrecy Act — 31 CFR 103.22 Currency Transaction Report"],
            },
            "forex": {
                "recommended_provider": "JP Morgan Treasury",
                "recommended_rate": 0.9997,
                "estimated_savings_usd": 15.0,
                "timing": "EXECUTE_NOW",
                "currency_pair": "USD/USD",
            },
            "liquidity": {
                "status": "SUFFICIENT",
                "available_balance": 1420000.0,
                "post_payment_balance": 1370000.0,
                "covenant_at_risk": False,
                "recommended_action": "Sufficient liquidity. Proceed to FX execution.",
                "netting_available": False,
            },
            "risk": {
                "composite_score": 23.4,
                "risk_level": "LOW",
                "limit_breaches": [],
                "factor_scores": {
                    "COUNTERPARTY": 35.0,
                    "CONCENTRATION": 0.6,
                    "MARKET": 15.0,
                    "OPERATIONAL": 45.0,
                },
                "mitigations": [],
            },
            "decision": {
                "decision": "AUTO_EXECUTE",
                "escalation_level": None,
                "execution_route": "JP Morgan Treasury",
                "summary": "Payment approved for automatic execution. All compliance, risk, and liquidity checks passed.",
                "confidence": 1.0,
            },
        },
        "processing_error": None,
        "warnings": [],
    },
]


# ── Demo case ──────────────────────────────────────────────────────────────────

DEMO_CASES = [
    {
        "case_id": "CASE-DEMO-001",
        "upload_id": "DEMO0003",
        "payment_id": "PAY-Q2-002",
        "title": "PAY-Q2-002 requires CFO review — £2.1M acquisition payment",
        "case_type": "PAYMENT_ESCALATION",
        "priority": "HIGH",
        "assigned_role": "CFO",
        "status": "OPEN",
        "risk_score": 71.2,
        "amount": 2100000.0,
        "currency": "GBP",
        "counterparty": "Manchester Industrial Holdings PLC",
        "created_at": "2026-06-15T08:41:00Z",
        "updated_at": "2026-06-15T08:41:00Z",
        "closed_at": None,
        "reviewer": None,
        "reviewer_notes": None,
        "sla_minutes": 240,
        "payload": {
            "decision_summary": (
                "High-value acquisition payment (£2,100,000 GBP) exceeds materiality "
                "threshold. Risk score 71.2 — elevated due to counterparty concentration "
                "and large single-transaction exposure. Compliance CLEAR. FX route via "
                "Barclays Markets saves estimated £3,150. Requires CFO sign-off per "
                "Treasury Policy §4.2."
            ),
            "compliance_decision": "CLEAR",
            "fx_savings": 3150.0,
            "liquidity_status": "SUFFICIENT",
            "risk_level": "MEDIUM",
            "escalation_rationale": [
                "Payment amount £2,100,000 exceeds CFO materiality threshold of £1,000,000",
                "Purpose: ACQUISITION — additional scrutiny required per Treasury Policy",
                "Composite risk score 71.2 in MEDIUM-HIGH band",
            ],
        },
    },
]


# ── Demo audit events ──────────────────────────────────────────────────────────

DEMO_AUDIT = [
    {
        "event_id": "evt-demo-005",
        "event_type": "CASE_CREATED",
        "timestamp": "2026-06-15T08:41:05Z",
        "actor": "system",
        "upload_id": "DEMO0003",
        "case_id": "CASE-DEMO-001",
        "description": (
            "Maestro case CASE-DEMO-001 created: PAY-Q2-002 escalated to CFO"
        ),
        "details": {"risk_score": 71.2, "amount": 2100000.0},
    },
    {
        "event_id": "evt-demo-004",
        "event_type": "PIPELINE_COMPLETE",
        "timestamp": "2026-06-15T08:41:00Z",
        "actor": "system",
        "upload_id": "DEMO0003",
        "case_id": "CASE-DEMO-001",
        "description": "Pipeline complete: JSON Payment (4 records validated, ESCALATE triggered for PAY-Q2-002)",
        "details": {"decision": "ESCALATE", "risk_score": 71.2},
    },
    {
        "event_id": "evt-demo-003",
        "event_type": "FILE_UPLOADED",
        "timestamp": "2026-06-15T08:40:00Z",
        "actor": "treasury@nexusglobal.com",
        "upload_id": "DEMO0003",
        "case_id": None,
        "description": "File uploaded: treasury_payments_q2_demo.json (2.0 KB)",
        "details": {
            "filename": "treasury_payments_q2_demo.json",
            "size_bytes": 2050,
            "file_type": "JSON Payment",
        },
    },
    {
        "event_id": "evt-demo-002",
        "event_type": "FILE_UPLOADED",
        "timestamp": "2026-06-15T08:35:00Z",
        "actor": "treasury@nexusglobal.com",
        "upload_id": "DEMO0002",
        "case_id": None,
        "description": "File uploaded: batch_payments_june_demo.csv (1.1 KB)",
        "details": {
            "filename": "batch_payments_june_demo.csv",
            "size_bytes": 1131,
            "file_type": "CSV Batch",
        },
    },
    {
        "event_id": "evt-demo-001",
        "event_type": "FILE_UPLOADED",
        "timestamp": "2026-06-15T08:30:00Z",
        "actor": "treasury@nexusglobal.com",
        "upload_id": "DEMO0001",
        "case_id": None,
        "description": "File uploaded: sample_swift_mt103_demo.txt (410 B)",
        "details": {
            "filename": "sample_swift_mt103_demo.txt",
            "size_bytes": 410,
            "file_type": "SWIFT MT103",
        },
    },
]


# ── Main ───────────────────────────────────────────────────────────────────────

def reset() -> None:
    # Ensure directories exist
    UPLOAD_HISTORY.parent.mkdir(parents=True, exist_ok=True)
    CASES_FILE.parent.mkdir(parents=True, exist_ok=True)

    UPLOAD_HISTORY.write_text(json.dumps(DEMO_UPLOADS, indent=2), encoding="utf-8")
    print(f"[OK] upload_history.json  — {len(DEMO_UPLOADS)} demo uploads")

    CASES_FILE.write_text(json.dumps(DEMO_CASES, indent=2), encoding="utf-8")
    print(f"[OK] cases.json           — {len(DEMO_CASES)} demo case(s)")

    AUDIT_FILE.write_text(json.dumps(DEMO_AUDIT, indent=2), encoding="utf-8")
    print(f"[OK] audit.json           — {len(DEMO_AUDIT)} demo events")

    print()
    print("Demo state reset. Open http://localhost:8000 and follow DEMO.md.")


if __name__ == "__main__":
    reset()
