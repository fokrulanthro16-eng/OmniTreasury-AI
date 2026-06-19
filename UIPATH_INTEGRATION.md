# UiPath Integration Guide

**OmniTreasury AI — UiPath AgentHack 2026**

---

## Overview

OmniTreasury AI integrates with UiPath at two levels:

| Level | What it does | Requires |
|---|---|---|
| **Maestro Case (demo mode)** | Auto-creates cases locally on ESCALATE, full lifecycle management in web UI | Nothing — works out of the box |
| **Maestro Case (live mode)** | Creates real Maestro Cases via REST API with OAuth2 | UiPath Cloud credentials in `.env` |
| **Studio Python Activity** | Embeds OmniTreasury as a Python Script activity in a UiPath workflow | `main.py` + `uipath_process_payment()` |

---

## Part 1 — Maestro Case Integration

### How It Works

When the OmniTreasury AI pipeline returns `ESCALATE`, the following happens automatically in `src/web/routers/processing.py`:

```python
if decision.decision.value == "ESCALATE":
    case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
    assigned_role = decision.escalation_level.value   # CFO / TREASURY_MANAGER / etc.
    priority = "HIGH" if float(payment.amount) >= 500_000 else "MEDIUM"
    sla_map = {
        "CFO": 240,               # 4 hours
        "TREASURY_MANAGER": 120,  # 2 hours
        "COMPLIANCE_OFFICER": 60, # 1 hour
        "LEGAL": 480,             # 8 hours
    }
    store.upsert_case({ case_id, upload_id, payment_id, title, ... })
    store.add_audit("CASE_CREATED", ...)
    result["case_id"] = case_id
```

### Escalation Role Assignment

| Trigger condition | Assigned role | SLA |
|---|---|---|
| Amount ≥ materiality threshold (default £1M) | `CFO` | 240 min |
| Risk score ≥ 60 or liquidity insufficient | `TREASURY_MANAGER` | 120 min |
| Compliance FLAG (sanctions proximity / AML) | `COMPLIANCE_OFFICER` | 60 min |
| Legal / jurisdiction risk | `LEGAL` | 480 min |

### Case Payload

Every Maestro case includes a `payload` object — the complete evidence bundle:

```json
{
  "decision_summary": "High-value acquisition payment exceeds CFO threshold...",
  "compliance_decision": "CLEAR",
  "fx_savings": 3150.0,
  "liquidity_status": "SUFFICIENT",
  "risk_level": "MEDIUM",
  "escalation_rationale": [
    "Payment amount £2,100,000 exceeds CFO materiality threshold of £1,000,000",
    "Purpose: ACQUISITION — additional scrutiny required per Treasury Policy",
    "Composite risk score 71.2 in MEDIUM-HIGH band"
  ]
}
```

### Case Lifecycle API

All lifecycle transitions are managed via `PATCH /api/cases/{case_id}`:

```bash
# Move to review
curl -X PATCH http://localhost:8000/api/cases/CASE-DEMO-001 \
  -H "Content-Type: application/json" \
  -d '{"status": "UNDER_REVIEW", "reviewer": "Sarah Chen CFO"}'

# Approve
curl -X PATCH http://localhost:8000/api/cases/CASE-DEMO-001 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "APPROVED",
    "reviewer": "Sarah Chen CFO",
    "reviewer_notes": "Board resolution on file. Counterparty due diligence complete."
  }'

# Reject
curl -X PATCH http://localhost:8000/api/cases/CASE-DEMO-001 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "REJECTED",
    "reviewer": "Sarah Chen CFO",
    "reviewer_notes": "Insufficient documentation for acquisition payment."
  }'
```

State machine — only listed transitions are valid (others return HTTP 422):

```
OPEN → UNDER_REVIEW → APPROVED → CLOSED
                    ↘ REJECTED → CLOSED
```

---

## Part 2 — Live Maestro API (Production Mode)

### Setup

Set the following in your `.env` file:

```env
USE_MOCK_MAESTRO=false
UIPATH_ORG_ID=your_organisation_id
UIPATH_TENANT_NAME=your_tenant_name
UIPATH_CLIENT_ID=your_oauth2_client_id
UIPATH_CLIENT_SECRET=your_oauth2_client_secret
```

### OAuth2 Authentication

The integration in `src/integrations/uipath_maestro.py` authenticates via the UiPath Identity Server:

```
POST https://cloud.uipath.com/identity_/connect/token
  grant_type=client_credentials
  client_id={UIPATH_CLIENT_ID}
  client_secret={UIPATH_CLIENT_SECRET}
  scope=OR.Cases
```

The token is cached and refreshed automatically on expiry.

### Case Creation (Live)

```
POST https://cloud.uipath.com/{ORG}/{TENANT}/orchestrator_/api/Maestro/Cases
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "PAY-Q2-002 requires CFO review — £2.1M acquisition payment",
  "priority": "High",
  "assignedRole": "CFO",
  "slaMinutes": 240,
  "customData": { ...evidence_payload... }
}
```

### Switching Back to Demo Mode

```env
USE_MOCK_MAESTRO=true
```

No other changes required. The local case store (`data/cases.json`) picks up immediately.

---

## Part 3 — UiPath Studio Integration

### Option A — Python Script Activity (simplest)

In UiPath Studio, add a **Python Script** activity pointing to this repository:

```python
import sys
sys.path.insert(0, r"C:\path\to\OmniTreasury_AI")
from main import uipath_process_payment

# payment_id is a variable from your ERP workflow
result_json = uipath_process_payment(in_PaymentId)
# result_json is a JSON string you can assign to out_Result
```

The function returns a JSON string with:

```json
{
  "payment_id": "PAY-2026-0002",
  "decision": "ESCALATE",
  "escalation_level": "CFO",
  "case_payload": {
    "compliance_decision": "CLEAR",
    "risk_score": 71.2,
    "fx_savings": 3150.0,
    "liquidity_status": "SUFFICIENT",
    "escalation_rationale": ["..."]
  },
  "execution_route": null,
  "confidence": 0.95
}
```

Use an **Assign** activity to deserialise: `JObject.Parse(out_Result)["decision"].ToString()`

### Option B — REST API from Studio (recommended for production)

UiPath Studio can call the OmniTreasury REST API directly using the **HTTP Request** activity:

```
Step 1 — Upload file
  HTTP POST http://omnitreasury-host:8000/api/upload
  Body: multipart/form-data  file={payment_file}
  → capture upload_id from response

Step 2 — Run pipeline
  HTTP POST http://omnitreasury-host:8000/api/process-upload/{upload_id}
  → capture decision, case_id from response

Step 3 — Branch on decision
  If decision == "AUTO_EXECUTE"  → mark workflow complete
  If decision == "HARD_REJECT"   → trigger rejection workflow
  If decision == "ESCALATE"      → poll /api/cases/{case_id} for human decision
```

### Option C — Webhook / Polling Pattern

For ERP-triggered processing, set up a UiPath Robot to:

1. Watch for new payment files in a SharePoint / network folder
2. POST each file to `/api/upload`
3. POST to `/api/process-upload/{id}`
4. If `case_id` returned → enter polling loop on `GET /api/cases/{case_id}`
5. When `status` reaches `APPROVED` or `REJECTED` → trigger downstream ERP update

---

## Part 4 — Demo Workflow (No Credentials Required)

The demo scenario in [DEMO.md](DEMO.md) uses the local case store and requires no UiPath credentials. The full Maestro lifecycle — case creation, status updates, reviewer notes, audit trail — is fully functional in demo mode.

To trigger an escalation from scratch (rather than using the seeded case):

1. Upload a SWIFT MT103 with amount > £1,000,000 in the `:32A:` field
2. Click **Process** — the pipeline will return `ESCALATE` and auto-create a case
3. Navigate to **Cases** to see the new case and manage its lifecycle

A SWIFT MT103 template for a high-value payment:

```
{1:F01CORPGB2LXXXX0000000000}
{2:I103NWBKGB2LXXXXN}
{4:
:20:TXN-2026-TEST-HV
:23B:CRED
:32A:260621GBP2100000,00
:50K:/GB29NWBK60161331926819
NEXUS GLOBAL CORPORATION EMEA
:59:/GB98MIDL07009312345678
MANCHESTER INDUSTRIAL HOLDINGS PLC
MANCHESTER M1 5AN GB
:70:ACQUISITION PAYMENT REF ACQ-2026-007
:71A:SHA
-}
```

Save as a `.txt` file and upload it. The £2,100,000 amount will trigger a CFO escalation.

---

## Part 5 — Evidence Audit Trail

Every case created by OmniTreasury AI produces a queryable audit chain:

```bash
# All events for a specific case
GET /api/audit?case_id=CASE-DEMO-001

# All events for a specific upload
GET /api/audit?upload_id=DEMO0003

# Last 100 events across the system
GET /api/audit?limit=100
```

This audit trail satisfies:
- **Basel III** operational risk documentation requirements
- **SOX** internal control audit requirements
- **Bank Secrecy Act** transaction monitoring documentation
- **FATF Recommendation 16** correspondent banking record-keeping

Each event records: `event_id`, `event_type`, `timestamp` (UTC), `actor`, `upload_id`, `case_id`, `description`, and a `details` payload.

---

*OmniTreasury AI — UiPath Integration Guide — AgentHack 2026*
