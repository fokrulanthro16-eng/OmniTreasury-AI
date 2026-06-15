"""Generate demo upload files and populate the upload registry.

Run this once to seed the Data Upload Center with realistic demo content:

    python scripts/generate_upload_demo.py

Creates:
  sample_data/uploads/registry.json        (upload history for the dashboard)
  sample_data/uploads/sample_swift_mt103_demo.txt
  sample_data/uploads/batch_payments_june_demo.csv
  sample_data/uploads/treasury_payments_q2_demo.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Resolve project root
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

UPLOAD_DIR = ROOT / "sample_data" / "uploads"

SWIFT_CONTENT = """{1:F01DEUTDEFFAXXX0000000000}{2:I103CHASUS33XXXXN}{4:
:20:TXN-2026-DEMO-001
:23B:CRED
:32A:260617USD50000,00
:50K:/DE89370400440532013000
NEXUS GLOBAL CORPORATION
FRANKFURT AM MAIN
GERMANY
:52A:DEUTDEFFXXX
:57A:CHASUS33
:59:/US0900040012345678
ACME MANUFACTURING INC
NEW YORK NY 10001
UNITED STATES
:70:INV-2026-ACM-DEMO-001 TRADE PAYMENT Q2 2026
:71A:SHA
:72:/ACC/DEMO UPLOAD VIA OMNITREASURY AI DASHBOARD
-}
"""

CSV_CONTENT = """payment_id,source_entity,source_currency,amount,target_currency,counterparty_name,bank_country,value_date,purpose,urgency,submitted_by
PAY-BATCH-001,CORP-HQ,EUR,75000.00,USD,Acme Supplies GmbH,DE,2026-06-18,TRADE_PAYMENT,T_PLUS_2,treasury@nexusglobal.com
PAY-BATCH-002,CORP-EMEA,GBP,120000.00,USD,London Tech Partners Ltd,GB,2026-06-18,SERVICES,T_PLUS_2,emea.ops@nexusglobal.com
PAY-BATCH-003,CORP-APAC,SGD,35000.00,USD,Nexus Global Corporation,US,2026-06-17,DIVIDEND,T_PLUS_2,cfo.apac@nexusglobal.com
PAY-BATCH-004,CORP-HQ,USD,250000.00,EUR,Berlin Industrial KG,DE,2026-06-19,TRADE_PAYMENT,T_PLUS_2,procurement@nexusglobal.com
PAY-BATCH-005,CORP-EMEA,EUR,45000.00,GBP,Edinburgh Logistics Ltd,GB,2026-06-18,TRADE_PAYMENT,T_PLUS_1,emea.ops@nexusglobal.com
PAY-BATCH-006,CORP-HQ,USD,890000.00,JPY,Tokyo Components Corp,JP,2026-06-20,TRADE_PAYMENT,FLEXIBLE,japan.ops@nexusglobal.com
PAY-BATCH-007,CORP-LATAM,USD,18500.00,BRL,Sao Paulo Distributors SA,BR,2026-06-19,TRADE_PAYMENT,T_PLUS_2,latam.ops@nexusglobal.com
PAY-BATCH-008,CORP-APAC,USD,62000.00,SGD,SingTech Holdings Pte,SG,2026-06-18,SERVICES,T_PLUS_2,apac.ops@nexusglobal.com
"""

JSON_CONTENT = {
    "_comment": "Demo upload — Q2 2026 treasury payment batch uploaded via OmniTreasury AI dashboard",
    "batch_id": "BATCH-Q2-2026-DEMO",
    "uploaded_at": "2026-06-15T07:31:00Z",
    "submitted_by": "cfo@nexusglobal.com",
    "payments": [
        {
            "payment_id": "PAY-Q2-001",
            "source_entity": "CORP-HQ",
            "source_currency": "EUR",
            "amount": 95000.00,
            "target_currency": "USD",
            "counterparty": {"name": "Alpine Precision Engineering GmbH", "bank_country": "CH"},
            "value_date": "2026-06-20",
            "purpose": "TRADE_PAYMENT",
        },
        {
            "payment_id": "PAY-Q2-002",
            "source_entity": "CORP-EMEA",
            "source_currency": "GBP",
            "amount": 2100000.00,
            "target_currency": "USD",
            "counterparty": {"name": "Manchester Industrial Holdings PLC", "bank_country": "GB"},
            "value_date": "2026-06-21",
            "purpose": "ACQUISITION",
        },
        {
            "payment_id": "PAY-Q2-003",
            "source_entity": "CORP-APAC",
            "source_currency": "SGD",
            "amount": 480000.00,
            "target_currency": "USD",
            "counterparty": {"name": "Nexus Global Corporation", "bank_country": "US"},
            "value_date": "2026-06-18",
            "purpose": "DIVIDEND",
        },
        {
            "payment_id": "PAY-Q2-004",
            "source_entity": "CORP-HQ",
            "source_currency": "USD",
            "amount": 320000.00,
            "target_currency": "BRL",
            "counterparty": {"name": "Brasil Componentes SA", "bank_country": "BR"},
            "value_date": "2026-06-19",
            "purpose": "TRADE_PAYMENT",
        },
    ],
}

REGISTRY: list[dict] = [
    {
        "upload_id": "F4A2C891",
        "original_name": "sample_swift_mt103_demo.txt",
        "saved_name": "20260615_F4A2C891_sample_swift_mt103_demo.txt",
        "file_type": "SWIFT MT103",
        "extension": ".txt",
        "size_bytes": len(SWIFT_CONTENT.encode()),
        "uploaded_at": "2026-06-15T07:42:01Z",
        "uploaded_by": "treasury@nexusglobal.com",
        "status": "processed",
        "metadata": {
            "transaction_ref": "TXN-2026-DEMO-001",
            "currency": "USD",
            "amount": "50000.00",
            "value_date": "2026-06-17",
            "ordering_customer": "NEXUS GLOBAL CORPORATION",
            "beneficiary": "ACME MANUFACTURING INC",
            "charges": "SHA",
        },
        "preview_rows": [
            {"Field": "20", "Value": "TXN-2026-DEMO-001"},
            {"Field": "32A", "Value": "260617USD50000,00"},
            {"Field": "71A", "Value": "SHA"},
        ],
        "errors": [],
    },
    {
        "upload_id": "B7D3E156",
        "original_name": "batch_payments_june_demo.csv",
        "saved_name": "20260615_B7D3E156_batch_payments_june_demo.csv",
        "file_type": "CSV Batch",
        "extension": ".csv",
        "size_bytes": len(CSV_CONTENT.encode()),
        "uploaded_at": "2026-06-15T07:38:22Z",
        "uploaded_by": "emea.ops@nexusglobal.com",
        "status": "processed",
        "metadata": {
            "row_count": 8,
            "column_count": 11,
            "payment_ids": [f"PAY-BATCH-00{i}" for i in range(1, 9)],
            "total_amount": 1495500.0,
        },
        "preview_rows": [
            {"payment_id": "PAY-BATCH-001", "amount": "75000.00", "counterparty_name": "Acme Supplies GmbH"},
            {"payment_id": "PAY-BATCH-002", "amount": "120000.00", "counterparty_name": "London Tech Partners Ltd"},
        ],
        "errors": [],
    },
    {
        "upload_id": "A1C9F024",
        "original_name": "treasury_payments_q2_demo.json",
        "saved_name": "20260615_A1C9F024_treasury_payments_q2_demo.json",
        "file_type": "JSON Payment",
        "extension": ".json",
        "size_bytes": len(json.dumps(JSON_CONTENT).encode()),
        "uploaded_at": "2026-06-15T07:31:45Z",
        "uploaded_by": "cfo@nexusglobal.com",
        "status": "processed",
        "metadata": {
            "record_count": 4,
            "payment_ids": ["PAY-Q2-001", "PAY-Q2-002", "PAY-Q2-003", "PAY-Q2-004"],
            "currencies": ["EUR", "GBP", "SGD", "USD"],
            "total_amount": 2995000.0,
        },
        "preview_rows": [],
        "errors": [],
    },
    {
        "upload_id": "D5E8B312",
        "original_name": "board_treasury_report_june2026.pdf",
        "saved_name": "20260615_D5E8B312_board_treasury_report_june2026.pdf",
        "file_type": "PDF Document",
        "extension": ".pdf",
        "size_bytes": 284672,
        "uploaded_at": "2026-06-15T07:18:09Z",
        "uploaded_by": "cfo@nexusglobal.com",
        "status": "processed",
        "metadata": {
            "is_valid_pdf": True,
            "title": "Treasury Operations Report — June 2026",
            "estimated_pages": 12,
            "size_kb": 278.0,
        },
        "preview_rows": [],
        "errors": [],
    },
]


def main() -> None:
    print(f"\nOmniTreasury AI — Upload Demo Generator")
    print(f"=" * 45)

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    print(f"  Upload directory: {UPLOAD_DIR}")

    # Write demo files
    files = {
        "sample_swift_mt103_demo.txt": SWIFT_CONTENT.encode(),
        "batch_payments_june_demo.csv": CSV_CONTENT.encode(),
        "treasury_payments_q2_demo.json": json.dumps(JSON_CONTENT, indent=2).encode(),
    }
    for name, content in files.items():
        path = UPLOAD_DIR / name
        path.write_bytes(content)
        print(f"  Created: {name} ({len(content)} bytes)")

    # Write registry
    registry_path = UPLOAD_DIR / "registry.json"
    registry_path.write_text(json.dumps(REGISTRY, indent=2), encoding="utf-8")
    print(f"  Created: registry.json ({len(REGISTRY)} entries)")

    print(f"\n  Done. Open demo_output/treasury_control_tower.html to see the upload page.\n")


if __name__ == "__main__":
    main()
