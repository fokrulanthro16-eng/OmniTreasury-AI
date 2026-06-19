# OmniTreasury AI — Architecture

---

## 1. System Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER                                                         │
│                                                                             │
│  Browser SPA (index.html)                  /api/docs (Swagger UI)          │
│  11 pages · dark theme · vanilla JS        Interactive endpoint explorer   │
│  Auto-refresh every 15 s                                                    │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │  HTTP / JSON
┌─────────────────────────────▼───────────────────────────────────────────────┐
│  API LAYER  (FastAPI 0.136 + Uvicorn 0.34)                                  │
│                                                                             │
│  upload.py       GET /api/uploads  POST /api/upload  DELETE /api/uploads   │
│  processing.py   POST /api/process-upload/{id}                              │
│  cases.py        GET /api/cases  GET /api/cases/{id}  PATCH /api/cases/{id} │
│  audit.py        GET /api/audit                                             │
│  metrics.py      GET /api/metrics                                           │
│  upload.py       GET /api/health                                            │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────────────┐
│  SERVICE LAYER                                                              │
│                                                                             │
│  FileProcessor         Multi-format ingestion: SWIFT MT103 / CSV / JSON / PDF │
│  swift_mt103.py        Full field parser: :20: :23B: :32A: :50K: :59: :70: │
│                                                                             │
│  5-ENGINE PIPELINE (chained, deterministic)                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                                                                      │  │
│  │  ComplianceEngine     sanctions fuzzy-match · AML patterns           │  │
│  │       ↓               jurisdiction screening · confidence score      │  │
│  │  ForexEngine          5-provider rate ranking · timing optimisation  │  │
│  │       ↓               benchmark comparison · savings estimation      │  │
│  │  LiquidityEngine      covenant-aware balance check                   │  │
│  │       ↓               netting opportunity discovery                  │  │
│  │  RiskEngine           4-factor composite score (0–100)               │  │
│  │       ↓               counterparty · concentration · market · ops    │  │
│  │  DecisionEngine       policy matrix → AUTO_EXECUTE / ESCALATE /      │  │
│  │                       HARD_REJECT · rationale list                   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────────────┐
│  PERSISTENCE LAYER                                                          │
│                                                                             │
│  history.py            sample_data/uploads/upload_history.json              │
│                        Thread-safe · newest-first · upsert by upload_id    │
│                                                                             │
│  store.py              data/cases.json    — Maestro case records           │
│                        data/audit.json   — Immutable audit event log       │
│                        Two threading.Lock() — one per store                │
│                        _CASE_LOCK / _AUDIT_LOCK                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Data Flow — SWIFT MT103 Auto-Execute Path

```
User uploads sample_swift_mt103_demo.txt
        │
        ▼
POST /api/upload
  FileProcessor.process(filename, bytes)
  → upload_id generated (8-char hex)
  → SWIFT MT103 fields parsed
  → metadata extracted
  → record saved to upload_history.json (status: "uploaded")
  → FILE_UPLOADED audit event written
        │
        ▼
POST /api/process-upload/{upload_id}
  data = read file from disk
  parse_mt103(text) → PaymentRecord
        │
        ├── ComplianceEngine.run(payment)
        │       sanctions_list.json fuzzy-match (threshold: 75)
        │       AML pattern check (>$10k, structuring)
        │       FATF jurisdiction lookup
        │       → ComplianceResult(decision=CLEAR, confidence=0.97)
        │
        ├── ForexEngine.run(payment)
        │       fx_rates.json benchmark lookup
        │       5 provider quotes generated
        │       ranked by effective rate
        │       → FXResult(provider="JP Morgan", rate=0.9997, savings=$15)
        │
        ├── LiquidityEngine.run(payment)
        │       liquidity_positions.json entity lookup
        │       available_balance vs. payment.amount
        │       covenant headroom check
        │       netting counterparty scan
        │       → LiquidityResult(status=SUFFICIENT, balance=$1,420,000)
        │
        ├── RiskEngine.run(payment)
        │       counterparty risk (relationship, sanctions proximity)
        │       concentration risk (% of portfolio limit)
        │       market risk (currency volatility, geopolitical index)
        │       operational risk (settlement, documentation)
        │       → RiskResult(composite_score=23.4, level=LOW)
        │
        └── DecisionEngine.run(payment, compliance, forex, liquidity, risk)
                applies policy matrix:
                  CLEAR + score<60 + SUFFICIENT + amount<£1M → AUTO_EXECUTE
                → DecisionResult(decision=AUTO_EXECUTE, confidence=1.0)
        │
        ▼
  record["status"] = "processed"
  record["processing_result"] = full result dict
  hist.upsert(record)
  PIPELINE_COMPLETE audit event written
        │
        ▼
  Response: { success: true, file_id: "...", result: { ... } }
```

---

## 3. Data Flow — ESCALATE Path (Maestro Case Creation)

```
(Same steps 1–5 as above, but DecisionEngine returns ESCALATE)

DecisionEngine.run(...)
  amount >= £1M → ESCALATE, level=CFO
        │
        ▼
_run_swift_pipeline detects decision.value == "ESCALATE"

case_id = "CASE-" + uuid.hex[:8].upper()
assigned_role = decision.escalation_level.value  # "CFO"
priority = "HIGH"  (amount >= £500k)
sla_minutes = 240  (CFO SLA)

store.upsert_case({
    case_id, upload_id, payment_id,
    title, case_type, priority, assigned_role,
    status="OPEN", risk_score, amount, currency, counterparty,
    created_at, updated_at, closed_at=None,
    reviewer=None, reviewer_notes=None,
    sla_minutes,
    payload: {
        decision_summary, compliance_decision,
        fx_savings, liquidity_status, risk_level,
        escalation_rationale[0..2]
    }
})

store.add_audit("CASE_CREATED", ...)
result["case_id"] = case_id
record["linked_case_id"] = case_id
hist.upsert(record)
PIPELINE_COMPLETE audit event written
        │
        ▼
  Response: { success: true, file_id: "...", result: { ..., case_id: "CASE-..." } }
```

---

## 4. Data Flow — Case Lifecycle

```
PATCH /api/cases/CASE-DEMO-001
  body: { status: "UNDER_REVIEW", reviewer: "Sarah Chen" }
        │
        ▼
  get_case(case_id) from data/cases.json
  validate transition: OPEN → UNDER_REVIEW  ✓  (in _TRANSITIONS["OPEN"])
  case["status"] = "UNDER_REVIEW"
  case["reviewer"] = "Sarah Chen"
  case["updated_at"] = now_utc
  store.upsert_case(case)
  add_audit("CASE_UPDATED", actor="Sarah Chen")
        │
        ▼
PATCH /api/cases/CASE-DEMO-001
  body: { status: "APPROVED", reviewer_notes: "Board approval on file." }
        │
        ▼
  validate transition: UNDER_REVIEW → APPROVED  ✓
  case["status"] = "APPROVED"
  case["reviewer_notes"] = "Board approval on file."
  case["closed_at"] = now_utc
  store.upsert_case(case)
  add_audit("CASE_DECISION", actor="Sarah Chen")
```

**State machine (enforced in `cases.py`):**

```
         ┌─────────────────────────────────────┐
         │                                     │
    ─►  OPEN  ──►  UNDER_REVIEW  ──►  APPROVED  ──►  CLOSED
                              │
                              └──►  REJECTED  ──►  CLOSED
```

Any transition not in the map above returns `HTTP 422 Unprocessable Entity`.

---

## 5. Persistence Schema

### `upload_history.json` — one record per upload

```json
{
  "id": "DEMO0001",
  "filename": "sample_swift_mt103_demo.txt",
  "saved_as": "sample_swift_mt103_demo.txt",
  "file_type": "SWIFT MT103",
  "extension": ".txt",
  "size_bytes": 410,
  "uploaded_at": "2026-06-15T08:30:00Z",
  "status": "processed",
  "linked_case_id": null,
  "metadata": { "transaction_ref": "...", "amount": "50000.00", ... },
  "preview_rows": [ { "Field": "20", "Value": "TXN-2026-DEMO-001" }, ... ],
  "processing_result": { "pipeline": "SWIFT MT103", "payment": {...}, "decision": {...} },
  "processing_error": null,
  "warnings": []
}
```

### `data/cases.json` — one record per Maestro case

```json
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
  "closed_at": null,
  "reviewer": null,
  "reviewer_notes": null,
  "sla_minutes": 240,
  "payload": {
    "decision_summary": "...",
    "compliance_decision": "CLEAR",
    "fx_savings": 3150.0,
    "liquidity_status": "SUFFICIENT",
    "risk_level": "MEDIUM",
    "escalation_rationale": ["...", "...", "..."]
  }
}
```

### `data/audit.json` — one record per event

```json
{
  "event_id": "evt-demo-005",
  "event_type": "CASE_CREATED",
  "timestamp": "2026-06-15T08:41:05Z",
  "actor": "system",
  "upload_id": "DEMO0003",
  "case_id": "CASE-DEMO-001",
  "description": "Maestro case CASE-DEMO-001 created: PAY-Q2-002 escalated to CFO",
  "details": { "risk_score": 71.2, "amount": 2100000.0 }
}
```

**Audit event types:** `FILE_UPLOADED` · `PIPELINE_COMPLETE` · `CASE_CREATED` · `CASE_UPDATED` · `CASE_DECISION`

---

## 6. Threading Model

```
FastAPI / Uvicorn worker
    │
    ├── upload handler  ──────────────────────── _HISTORY_LOCK  (history.py)
    │
    ├── processing handler  ─┬── _CASE_LOCK   (store.py)
    │                        └── _AUDIT_LOCK  (store.py)
    │
    └── cases handler  ──────┬── _CASE_LOCK
                             └── _AUDIT_LOCK
```

Each lock is acquired for the minimum duration: read file → modify in memory → write file → release. No lock is held across network calls.

---

## 7. Engine Interface Contract

Every engine exposes exactly one public method:

```python
class ComplianceEngine:
    def run(self, payment: PaymentRecord) -> ComplianceResult: ...

class ForexEngine:
    def run(self, payment: PaymentRecord) -> FXResult: ...

class LiquidityEngine:
    def run(self, payment: PaymentRecord) -> LiquidityResult: ...

class RiskEngine:
    def run(self, payment: PaymentRecord) -> RiskResult: ...

class DecisionEngine:
    def run(
        self,
        payment: PaymentRecord,
        compliance: ComplianceResult,
        forex: FXResult,
        liquidity: LiquidityResult,
        risk: RiskResult,
    ) -> DecisionResult: ...
```

This interface is stable. Swapping a deterministic engine for a CrewAI LLM agent requires only that the agent exposes `.run()` returning the same Pydantic result model.

---

*OmniTreasury AI — Architecture — UiPath AgentHack 2026*
