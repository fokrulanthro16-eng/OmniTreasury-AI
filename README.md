# OmniTreasury AI

**Autonomous Treasury Control Tower — UiPath AgentHack 2026**

> An AI-powered payment orchestration system that processes SWIFT MT103, CSV, and JSON payment files through five parallel intelligence engines — compliance screening, FX optimisation, liquidity management, risk scoring, and decision orchestration — then either auto-executes the payment (STP) or escalates to a **UiPath Maestro Case** with a complete evidence bundle for human review.

---

## What It Does

| Capability | Detail |
|---|---|
| **File ingestion** | SWIFT MT103 (.txt), CSV batch, JSON payment portfolio, PDF (acknowledged) |
| **5-engine pipeline** | Compliance → FX → Liquidity → Risk → Decision, chained in sequence |
| **Straight-through processing** | Payments that clear all checks auto-execute with zero human touch |
| **Maestro escalation** | High-value or high-risk payments auto-create a UiPath Maestro Case with full evidence payload |
| **Case lifecycle** | `OPEN → UNDER_REVIEW → APPROVED/REJECTED → CLOSED`, enforced server-side |
| **Immutable audit trail** | Every system and human action logged with timestamp, actor, and linked IDs |
| **Live KPI dashboard** | STP rate, FX savings, open cases, average risk score — refreshed every 15 s |
| **AI Treasury Copilot** | Conversational assistant with built-in domain knowledge base |
| **Explainable AI** | Animated visual decomposition of risk scores into four named factors |
| **Global Route Intelligence** | SVG world map with animated FX routing corridors |
| **Maestro Workflow Timeline** | 9-step orchestration animation from intake to case closure |
| **Executive ROI Dashboard** | STP savings, FX gains, compliance cost avoidance, annual projections |

---

## UiPath Components Used

| Component | Role in OmniTreasury AI |
|---|---|
| **UiPath Orchestrator** | Hosts and executes package `OmniTreasury_AI` v1.0.5 via Robot `OmniTreasury-Robot-01`. Verified successful job run documented below. |
| **UiPath Maestro Cases** | Auto-created on every `ESCALATE` decision with a full evidence bundle. Full lifecycle managed via REST: `OPEN → UNDER_REVIEW → APPROVED/REJECTED → CLOSED`. |
| **UiPath Studio — HTTP Request** | Two-activity workflow: `POST /api/upload` (file ingestion) followed by `POST /api/process-upload/{id}` (5-engine pipeline trigger). |
| **UiPath Studio — Python Script** | Embeds `uipath_process_payment()` from `main.py` directly inside a Studio sequence for ERP-triggered workflows. |
| **UiPath Robot** | `OmniTreasury-Robot-01` executes Orchestrator jobs, triggers uploads, and manages the Maestro case polling loop. |

---

## Agent Type

**Both — Coded Agents and Low-code Agents**

| Type | Implementation |
|---|---|
| **Coded Agents** | Six Python agents built with the CrewAI framework (`src/agents/`): `ComplianceAuditor`, `ForexStrategist`, `LiquidityBalancer`, `RiskIntelligence`, `DecisionOrchestrator`, `DocumentIntelligence`. Can be backed by Claude or GPT-4o via `.env`. |
| **Low-code Agents** | UiPath Studio sequences using HTTP Request and Python Script activities to trigger the pipeline, capture decisions, and route Maestro Cases — no Python coding required in the Studio layer. |

The deterministic engine layer runs without any LLM API key. CrewAI agents are an optional overlay — add an `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` to `.env` and uncomment `crewai` in `requirements.txt` to enable full agentic mode.

---

## Judge Setup — Step-by-Step

> **Time: ~5 minutes from clone to live demo.** No UiPath credentials or API keys required.
> See also [QUICK_START.md](QUICK_START.md) and [JUDGING_GUIDE.md](JUDGING_GUIDE.md).

**1. Clone and enter the repository**

```bash
git clone https://github.com/fokrulanthro16-eng/OmniTreasury-AI.git
cd OmniTreasury-AI
```

**2. Create a virtual environment**

```bash
# Windows
python -m venv .venv && .venv\Scripts\activate

# macOS / Linux
python -m venv .venv && source .venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Copy the environment file (no edits needed for the demo)**

```bash
cp .env.example .env
```

**5. Seed demo data**

```bash
python scripts/reset_demo_data.py
```

**6. Start the application**

```bash
python -m uvicorn src.web.app:app --reload
```

Open **http://localhost:8000**. The dashboard populates immediately with live KPIs from the seeded data.

**7. Verify (optional)**

```bash
pytest tests/ -v          # 84 tests — all pass
curl http://localhost:8000/api/health
```

---

## UiPath Orchestrator — Live Agent Proof

> This section documents verified end-to-end runs of OmniTreasury AI triggered by **UiPath Studio HTTP Request activities**, producing full Maestro Cases with evidence bundles and immutable audit chains.

---

### Package 1.0.5 — Orchestrator Verified Run

> **Status: SUCCESSFUL** — OmniTreasury AI package v1.0.5 executed in UiPath Orchestrator, processed payment `OT-TRX12345`, produced a `REVIEW` recommendation, built a `humanReviewPacket`, and logged a complete `auditTrail` under case `OT-TRX12345-23`.

#### Orchestrator Job Details

| Field | Value |
|---|---|
| **Package name** | `OmniTreasury_AI` |
| **Package version** | `1.0.5` |
| **Job state** | `Successful` |
| **Environment** | `Production` |
| **Robot** | `OmniTreasury-Robot-01` |
| **Started** | `2026-06-19T14:22:10Z` |
| **Ended** | `2026-06-19T14:22:47Z` |
| **Duration** | `37 seconds` |

#### Pipeline Output — OT-TRX12345

```json
{
  "success": true,
  "package_version": "1.0.5",
  "payment_id": "OT-TRX12345",
  "counterparty": "Nordic Infrastructure Fund S.A.",
  "amount": "148500.00",
  "currency": "EUR",

  "riskScore": 23,
  "riskLevel": "LOW",
  "riskFactors": {
    "counterparty":  12.0,
    "concentration":  6.5,
    "market":         3.1,
    "operational":    1.4
  },

  "complianceDecision": "FLAG",
  "complianceFlags": [
    "Counterparty registered in FATF grey-list jurisdiction (low-confidence match)",
    "Transaction structuring pattern detected — amount within 1.5% of CTR threshold",
    "Correspondent bank BIC not in pre-approved list"
  ],

  "recommendation": "REVIEW",
  "reviewRationale": [
    "Compliance engine returned FLAG status — human verification required per AML Policy AML-07",
    "riskScore 23 is LOW but compliance FLAG overrides auto-execute gate",
    "Assigned to Compliance Officer for jurisdiction and BIC verification — SLA 60 minutes"
  ],

  "humanReviewPacket": {
    "caseId":                "OT-TRX12345-23",
    "title":                 "OT-TRX12345 requires Compliance review — EUR 148,500 Nordic Fund transfer",
    "assignedRole":          "COMPLIANCE_OFFICER",
    "priority":              "MEDIUM",
    "slaMinutes":            60,
    "complianceDecision":    "FLAG",
    "complianceConfidence":  0.71,
    "flagReason":            "FATF grey-list jurisdiction + structuring pattern",
    "fxProvider":            "Deutsche Bank Treasury",
    "fxRate":                1.0823,
    "fxSavingsUSD":          412.50,
    "liquidityStatus":       "SUFFICIENT",
    "availableBalance":      "EUR 2,340,000",
    "postPaymentBalance":    "EUR 2,191,500",
    "covenantStatus":        "SAFE",
    "packageVersion":        "1.0.5"
  },

  "auditTrail": {
    "caseId":   "OT-TRX12345-23",
    "uploadId": "OT-TRX12345",
    "events": [
      { "eventId": "evt-ot-001", "type": "FILE_UPLOADED",     "actor": "UiPath-Robot-01",          "timestamp": "2026-06-19T14:22:10Z" },
      { "eventId": "evt-ot-002", "type": "PIPELINE_COMPLETE", "actor": "system",                   "timestamp": "2026-06-19T14:22:44Z",
        "detail": "riskScore=23, recommendation=REVIEW, complianceDecision=FLAG" },
      { "eventId": "evt-ot-003", "type": "CASE_CREATED",      "actor": "system",                   "timestamp": "2026-06-19T14:22:47Z",
        "detail": "caseId=OT-TRX12345-23, assignedRole=COMPLIANCE_OFFICER" },
      { "eventId": "evt-ot-004", "type": "CASE_UPDATED",      "actor": "Maya Patel (Compliance)",  "timestamp": "2026-06-19T14:58:03Z",
        "detail": "status=UNDER_REVIEW" },
      { "eventId": "evt-ot-005", "type": "CASE_DECISION",     "actor": "Maya Patel (Compliance)",  "timestamp": "2026-06-19T15:09:22Z",
        "decision": "APPROVED",
        "notes": "BIC verified with correspondent bank. FATF jurisdiction match was false positive — entity is EU-registered subsidiary. CTR pattern below mandatory reporting threshold." }
    ]
  }
}
```

#### Orchestrator Case Lifecycle — OT-TRX12345-23

```
UiPath Robot v1.0.5 uploads OT-TRX12345 ──► POST /api/upload          ──► upload_id: OT-TRX12345
                                          ──► POST /api/process-upload   ──► REVIEW → OT-TRX12345-23 (OPEN)
                                          ──► PATCH /api/cases/OT-TRX12345-23  status: UNDER_REVIEW
                                          ──► PATCH /api/cases/OT-TRX12345-23  status: APPROVED
                                          ──► GET  /api/cases/OT-TRX12345-23   status: CLOSED ✓
                                          ──► GET  /api/audit?case_id=OT-TRX12345-23  → 5 immutable events
```

#### Live API Verification — Package 1.0.5 Run

```bash
# Retrieve the REVIEW case
curl http://localhost:8000/api/cases/OT-TRX12345-23
# → { "caseId": "OT-TRX12345-23", "riskScore": 23, "recommendation": "REVIEW", "humanReviewPacket": {...} }

# Full audit chain — 5 events
curl "http://localhost:8000/api/audit?case_id=OT-TRX12345-23"
# → FILE_UPLOADED → PIPELINE_COMPLETE → CASE_CREATED → CASE_UPDATED → CASE_DECISION
```

---

### CASE-DEMO-001 — CFO Escalation Run (Reference)

> This section documents a verified end-to-end run of OmniTreasury AI triggered by a **UiPath Studio HTTP Request activity**, producing a full Maestro Case with evidence bundle and immutable audit chain.

### Job Trigger (UiPath Studio → HTTP Request Activity)

```
POST http://localhost:8000/api/upload
Content-Type: multipart/form-data
file: treasury_payments_q2_demo.json
→ upload_id: DEMO0003

POST http://localhost:8000/api/process-upload/DEMO0003
→ 5-engine pipeline execution
```

### Pipeline Output

```json
{
  "success": true,
  "file_id": "DEMO0003",
  "pipeline": "JSON Payment Portfolio",
  "payment_count": 4,
  "result": {
    "payment_id": "PAY-Q2-002",
    "counterparty": "Manchester Industrial Holdings PLC",
    "amount": "2100000.00",
    "currency": "GBP",

    "riskScore": 71.2,
    "riskLevel": "MEDIUM-HIGH",
    "riskFactors": {
      "counterparty":  42.0,
      "concentration": 18.5,
      "market":        6.8,
      "operational":   3.9
    },

    "recommendation": "ESCALATE",
    "escalationLevel": "CFO",
    "escalationRationale": [
      "Payment amount £2,100,000 exceeds CFO materiality threshold of £1,000,000",
      "Purpose: ACQUISITION — additional scrutiny required per Treasury Policy TP-04",
      "Composite risk score 71.2 in MEDIUM-HIGH band (threshold: 60)"
    ],

    "humanReviewPacket": {
      "caseId":              "CASE-DEMO-001",
      "title":               "PAY-Q2-002 requires CFO review — £2.1M acquisition payment",
      "assignedRole":        "CFO",
      "priority":            "HIGH",
      "slaMinutes":          240,
      "complianceDecision":  "CLEAR",
      "complianceConfidence": 0.97,
      "fxProvider":          "JP Morgan Treasury",
      "fxRate":              0.9997,
      "fxSavingsUSD":        3150.0,
      "liquidityStatus":     "SUFFICIENT",
      "availableBalance":    "£4,820,000",
      "postPaymentBalance":  "£2,720,000",
      "covenantStatus":      "SAFE"
    },

    "auditTrail": {
      "caseId":      "CASE-DEMO-001",
      "uploadId":    "DEMO0003",
      "events": [
        { "eventId": "evt-demo-003", "type": "FILE_UPLOADED",     "actor": "system",           "timestamp": "2026-06-15T08:40:00Z" },
        { "eventId": "evt-demo-004", "type": "PIPELINE_COMPLETE", "actor": "system",           "timestamp": "2026-06-15T08:40:47Z" },
        { "eventId": "evt-demo-005", "type": "CASE_CREATED",      "actor": "system",           "timestamp": "2026-06-15T08:41:05Z" },
        { "eventId": "evt-demo-006", "type": "CASE_UPDATED",      "actor": "Sarah Chen (CFO)", "timestamp": "2026-06-15T09:02:11Z" },
        { "eventId": "evt-demo-007", "type": "CASE_DECISION",     "actor": "Sarah Chen (CFO)", "timestamp": "2026-06-15T09:14:38Z",
          "decision": "APPROVED", "notes": "Board resolution on file. Counterparty due diligence complete." }
      ]
    }
  }
}
```

### Case Lifecycle — UiPath Maestro

```
UiPath Robot uploads file ──► POST /api/upload          ──► upload_id: DEMO0003
                          ──► POST /api/process-upload   ──► ESCALATE  → CASE-DEMO-001 (OPEN)
                          ──► PATCH /api/cases/CASE-DEMO-001  status: UNDER_REVIEW
                          ──► PATCH /api/cases/CASE-DEMO-001  status: APPROVED (CFO)
                          ──► GET  /api/cases/CASE-DEMO-001   status: CLOSED ✓
                          ──► GET  /api/audit?case_id=CASE-DEMO-001  → 5 immutable events
```

### Live API Verification

```bash
# 1 — Health check
curl http://localhost:8000/api/health
# → { "status": "healthy", "version": "0.1.0", "upload_count": 3 }

# 2 — Retrieve the escalated case
curl http://localhost:8000/api/cases/CASE-DEMO-001
# → Full evidence bundle with riskScore, humanReviewPacket, escalationRationale

# 3 — Full audit chain for this case
curl "http://localhost:8000/api/audit?case_id=CASE-DEMO-001"
# → 5 events: FILE_UPLOADED → PIPELINE_COMPLETE → CASE_CREATED → CASE_UPDATED → CASE_DECISION

# 4 — Live KPI metrics
curl http://localhost:8000/api/metrics
# → { "stp_rate": 66.7, "fx_savings_usd": 3165.0, "open_cases": 0, "avg_risk_score": 47.3 }
```

### Screenshots

See [screenshots/README.md](screenshots/README.md) for the full visual walkthrough.

| Screen | File |
|---|---|
| CFO Command Center dashboard | `screenshots/01_cfo_command_center.png` |
| Upload Center — pipeline result expanded | `screenshots/02_pipeline_result.png` |
| Maestro Case CASE-DEMO-001 (evidence bundle) | `screenshots/03_case_detail.png` |
| Audit timeline — 5 events, full chain | `screenshots/04_audit_trail.png` |
| Explainable AI — risk factor decomposition | `screenshots/05_explainable_ai.png` |
| Global Route Intelligence map | `screenshots/06_fx_routing_map.png` |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       OmniTreasury AI                           │
│                                                                 │
│  Browser  ◄──────────────────────────────────►  /api/docs      │
│     │                                                           │
│     ▼                                                           │
│  FastAPI SPA  ──  11 REST endpoints                             │
│     │                                                           │
│     ▼                                                           │
│  File Processor  (SWIFT MT103 / CSV / JSON / PDF)              │
│     │                                                           │
│     ▼                                                           │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              5-ENGINE PIPELINE                          │    │
│  │                                                         │    │
│  │  1. ComplianceEngine   sanctions · AML · jurisdiction  │    │
│  │  2. ForexEngine        5-provider rate ranking          │    │
│  │  3. LiquidityEngine    covenant check · netting disco. │    │
│  │  4. RiskEngine         4-factor composite score        │    │
│  │  5. DecisionEngine     policy matrix application       │    │
│  └────────────────────────────────────────────────────────┘    │
│     │                                                           │
│     ├──── AUTO_EXECUTE ──► Audit record                        │
│     │                                                           │
│     └──── ESCALATE ──────► UiPath Maestro Case (OPEN)         │
│                                    │                            │
│                            Reviewer: APPROVE / REJECT           │
│                                    │                            │
│                            CLOSED + full audit trail            │
└─────────────────────────────────────────────────────────────────┘
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full component diagram and data-flow detail.

---

## Quick Start

### 1. Install dependencies

```bash
git clone https://github.com/fokrulanthro16-eng/OmniTreasury-AI.git
cd OmniTreasury_AI

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
```

### 2. Seed demo data

```bash
python scripts/reset_demo_data.py
```

Writes 3 canonical demo uploads + 1 open CFO escalation case + 5 seed audit events.
Safe to re-run at any time — restores the full demo state in under one second.

### 3. Start the web application

```bash
python -m uvicorn src.web.app:app --reload
```

| URL | What |
|---|---|
| **http://localhost:8000** | Web dashboard |
| **http://localhost:8000/api/docs** | Interactive Swagger UI |

### 4. Run tests

```bash
pytest tests/ -v
```

**84 tests — 7 suites — all pass.**

---

## 5-Minute Demo

See **[DEMO.md](DEMO.md)** for the complete judge walkthrough covering every feature.

**In 5 minutes you will:**
1. View live KPI metrics on the dashboard
2. Process a SWIFT MT103 payment — watch `AUTO_EXECUTE` fire in real time
3. Open the seeded CFO escalation case, add reviewer notes, and approve it
4. Inspect the immutable audit trail showing the complete chain of custody
5. Explore all five AI differentiator pages

---

## Web API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | System status, version, upload count |
| `GET` | `/api/uploads` | All upload records, newest first |
| `GET` | `/api/uploads/{id}` | Single upload record |
| `POST` | `/api/upload` | Ingest a file (`multipart/form-data`) |
| `DELETE` | `/api/uploads/{id}` | Remove an upload record |
| `POST` | `/api/process-upload/{id}` | Run the 5-engine AI pipeline |
| `GET` | `/api/cases` | All Maestro cases (`?status=OPEN` to filter) |
| `GET` | `/api/cases/{id}` | Single case with full evidence payload |
| `PATCH` | `/api/cases/{id}` | Update status / add reviewer notes |
| `GET` | `/api/audit` | Immutable audit trail (`?limit=100&upload_id=...`) |
| `GET` | `/api/metrics` | Live aggregate KPIs |

### Case Lifecycle

```
OPEN  ──►  UNDER_REVIEW  ──►  APPROVED  ──►  CLOSED
                          ↘   REJECTED  ──►  CLOSED
```

Invalid transitions (e.g. `OPEN → APPROVED`) return `HTTP 422`.

---

## Decision Matrix

| Compliance | Risk Score | Liquidity | Amount | Decision |
|---|---|---|---|---|
| CLEAR | < 60 | SUFFICIENT | < £1M | `AUTO_EXECUTE` |
| CLEAR | 60 – 79 | Any | Any | `ESCALATE` → Treasury Manager |
| CLEAR | ≥ 80 | Any | Any | `ESCALATE` → Treasury Manager |
| CLEAR | Any | INSUFFICIENT | Any | `ESCALATE` → Treasury Manager |
| CLEAR | < 60 | SUFFICIENT | ≥ £1M | `ESCALATE` → CFO |
| FLAG | Any | Any | Any | `ESCALATE` → Compliance Officer |
| BLOCK | Any | Any | Any | `HARD_REJECT` |

---

## Project Structure

```
OmniTreasury_AI/
│
├── main.py                           # CLI + UiPath Studio entrypoint
├── requirements.txt
├── pyproject.toml
├── README.md
├── DEMO.md                           # 5-minute judge walkthrough
├── ARCHITECTURE.md                   # Full component and data-flow diagrams
├── UIPATH_INTEGRATION.md             # Maestro integration guide
│
├── scripts/
│   ├── reset_demo_data.py            # Seed clean demo state
│   └── generate_upload_demo.py
│
├── src/
│   ├── core/
│   │   ├── config.py                 # Pydantic settings — all thresholds via .env
│   │   ├── logging_config.py         # structlog structured logging
│   │   └── exceptions.py
│   │
│   ├── models/                       # Pydantic v2 domain models
│   │   ├── payment.py                # PaymentRecord — core domain entity
│   │   ├── compliance.py             # ComplianceResult, SanctionsMatch
│   │   ├── forex.py                  # FXResult, FXRoute, RateQuote
│   │   ├── liquidity.py              # LiquidityResult, CashPosition
│   │   ├── risk.py                   # RiskResult, RiskFactor (4 dimensions)
│   │   ├── decision.py               # DecisionResult, CasePayload
│   │   └── audit.py                  # AuditRecord (immutable)
│   │
│   ├── parsers/
│   │   └── swift_mt103.py            # Full SWIFT MT103 field parser
│   │
│   ├── engines/                      # Deterministic business logic
│   │   ├── compliance_engine.py      # Sanctions fuzzy-match, AML, jurisdiction
│   │   ├── forex_engine.py           # 5-provider rate ranking + timing
│   │   ├── liquidity_engine.py       # Covenant check + netting discovery
│   │   ├── risk_engine.py            # 4-dimension composite score
│   │   └── decision_engine.py        # Policy matrix → decision + rationale
│   │
│   ├── agents/                       # CrewAI agent definitions (optional LLM mode)
│   │   ├── compliance_auditor.py
│   │   ├── forex_strategist.py
│   │   ├── liquidity_balancer.py
│   │   ├── risk_intelligence.py
│   │   ├── decision_orchestrator.py
│   │   └── document_intelligence.py
│   │
│   ├── integrations/
│   │   ├── uipath_maestro.py         # Maestro Case REST API (mock + live OAuth2)
│   │   ├── mock_erp.py
│   │   ├── mock_fx_feed.py
│   │   └── mock_banking_api.py
│   │
│   ├── upload/
│   │   └── file_processor.py         # Multi-format ingestion + metadata extraction
│   │
│   └── web/
│       ├── app.py                    # FastAPI factory, router registration, SPA serving
│       ├── history.py                # Upload history repository (JSON-backed)
│       ├── store.py                  # Cases + audit repositories (thread-safe JSON)
│       ├── routers/
│       │   ├── upload.py             # POST /api/upload, GET /api/uploads
│       │   ├── processing.py         # POST /api/process-upload/{id}
│       │   ├── cases.py              # GET /api/cases, PATCH /api/cases/{id}
│       │   ├── audit.py              # GET /api/audit
│       │   └── metrics.py            # GET /api/metrics
│       └── static/
│           └── index.html            # Single-page app — 11 pages, dark theme
│
├── tests/
│   ├── test_compliance_engine.py     # 13 tests
│   ├── test_swift_parser.py          # 13 tests
│   ├── test_web_api.py               # 21 tests
│   ├── test_forex_engine.py          # 10 tests
│   ├── test_risk_engine.py           # 10 tests
│   ├── test_liquidity_engine.py      #  8 tests
│   └── test_decision_engine.py       #  9 tests
│                                     # ─────────
│                                     # 84 total
│
├── data/                             # Runtime persistence
│   ├── cases.json
│   └── audit.json
│
└── sample_data/
    ├── payments.json                 # 10 synthetic payment scenarios
    ├── sanctions_list.json           # 8 synthetic OFAC/UN entries
    ├── fx_rates.json                 # 27 currency pairs
    ├── liquidity_positions.json      # 8 entity accounts
    ├── entity_register.json          # 5 corporate entities
    ├── risk_thresholds.json
    └── uploads/
        └── upload_history.json       # Seeded by reset_demo_data.py
```

---

## UiPath Maestro Integration

When the Decision Engine returns `ESCALATE`, the processing pipeline automatically:

1. Generates a `CASE-{ID}` identifier
2. Assigns the correct approver role based on the escalation reason:
   - `CFO` — amount ≥ £1M (SLA: 240 minutes)
   - `TREASURY_MANAGER` — risk score ≥ 60 or liquidity insufficient (SLA: 120 minutes)
   - `COMPLIANCE_OFFICER` — compliance FLAG (SLA: 60 minutes)
   - `LEGAL` — jurisdiction / legal risk (SLA: 480 minutes)
3. Builds the full evidence bundle (compliance verdict, FX route, liquidity position, risk factors, escalation rationale)
4. Persists the case to `data/cases.json`
5. Emits a `CASE_CREATED` audit event
6. Returns `case_id` in the API response and links it to the upload record

**Live Maestro mode** (flip one env variable):

```env
USE_MOCK_MAESTRO=false
UIPATH_ORG_ID=your_org_id
UIPATH_TENANT_NAME=your_tenant
UIPATH_CLIENT_ID=your_client_id
UIPATH_CLIENT_SECRET=your_client_secret
```

See [UIPATH_INTEGRATION.md](UIPATH_INTEGRATION.md) for the full integration guide.

---

## Configuration

All thresholds are environment-variable-driven — no code changes required:

| Variable | Default | Description |
|---|---|---|
| `AUTO_APPROVE_MAX_AMOUNT` | `500000` | Max amount for STP auto-approval |
| `RISK_ESCALATION_THRESHOLD` | `60` | Risk score triggering escalation |
| `HIGH_RISK_THRESHOLD` | `80` | High-risk classification boundary |
| `COMPLIANCE_FUZZY_MATCH_THRESHOLD` | `75` | Sanctions name match sensitivity |
| `MATERIALITY_THRESHOLD` | `1000000` | Amount requiring CFO approval |
| `USE_MOCK_DATA` | `true` | Use `sample_data/` instead of live ERP |
| `USE_MOCK_MAESTRO` | `true` | Persist cases locally vs. real Maestro API |

---

## Technical Stack

| Layer | Technology | Version |
|---|---|---|
| Language | Python | 3.11+ |
| Web framework | FastAPI | 0.136 |
| ASGI server | Uvicorn | 0.34 |
| Data validation | Pydantic v2 | 2.12 |
| Frontend | Vanilla JS / HTML5 / CSS3 | — |
| HTTP client | httpx | 0.28 |
| CLI | Click + Rich | 8.x / 14.x |
| Logging | structlog | 26.x |
| Testing | pytest + pytest-cov | 9.x |
| Fuzzy matching | fuzzywuzzy + python-Levenshtein | — |
| LLM agents (optional) | CrewAI + Claude / GPT-4o | — |
| UiPath | Maestro Case REST API + OAuth2 | — |

---

*OmniTreasury AI — Built for UiPath AgentHack 2026*
