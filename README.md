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

## UiPath Orchestrator — Live Agent Proof

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
git clone https://github.com/fokrulanthro16/OmniTreasury_AI.git
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
