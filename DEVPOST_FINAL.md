# OmniTreasury AI — Final Devpost Submission

**UiPath AgentHack 2026**
**Category:** Agentic AI for Enterprise Automation

---

## Title

**OmniTreasury AI — Autonomous Treasury Control Tower with UiPath Maestro Human-in-the-Loop**

---

## Tagline (≤ 160 characters)

> AI pipeline that screens, optimises, and decides on cross-border payments — auto-executing clean ones and escalating high-risk payments to UiPath Maestro Cases for human review.

---

## GitHub Repository

```
https://github.com/YOUR_GITHUB_USERNAME/OmniTreasury_AI
```

*(Replace with actual URL after pushing — see GITHUB_PUSH.md)*

---

## Demo Video

*(Link to your recorded walkthrough following DEMO_VIDEO_SCRIPT.md)*

---

## What It Does

OmniTreasury AI is an autonomous treasury payment orchestration system that processes SWIFT MT103, CSV batch, and JSON payment portfolios through five chained AI engines, then either auto-executes the payment straight-through (STP) or creates a **UiPath Maestro Case** with a complete evidence bundle for human review.

### The 5-Engine Pipeline

1. **Compliance Engine** — sanctions fuzzy-match (fuzzywuzzy, 75% threshold), AML pattern detection (structuring, CTR thresholds), FATF jurisdiction screening → `CLEAR` / `FLAG` / `BLOCK`

2. **FX Engine** — benchmark rates for 27 currency pairs, quotes from 5 providers (JP Morgan, Deutsche Bank, Barclays, HSBC, Citi), ranked by effective rate, execution timing recommendation

3. **Liquidity Engine** — entity balance check against payment amount, covenant headroom validation, netting opportunity discovery to eliminate the FX leg

4. **Risk Engine** — 4-factor composite score (Counterparty / Concentration / Market / Operational) → 0–100, classified as LOW / MEDIUM / HIGH / CRITICAL

5. **Decision Engine** — policy matrix applied to all four results → `AUTO_EXECUTE`, `ESCALATE` (→ UiPath Maestro Case), or `HARD_REJECT`

### UiPath Maestro Integration — Verified Live Run

When the Decision Engine returns `ESCALATE`, OmniTreasury AI automatically:

- Generates a `CASE-{ID}` with assigned role (CFO / Treasury Manager / Compliance Officer / Legal) and SLA
- Builds a complete evidence bundle: compliance verdict, optimal FX provider + savings, liquidity position, 4-factor risk breakdown, escalation rationale
- Exposes the full case lifecycle via REST API (`OPEN → UNDER_REVIEW → APPROVED/REJECTED → CLOSED`) with server-enforced state machine
- Writes every event to an immutable audit trail (Basel III / SOX / BSA / FATF Rec.16 compliant)

**Verified pipeline output (CASE-DEMO-001 — £2.1M CFO escalation):**

```json
{
  "riskScore": 71.2,
  "riskLevel": "MEDIUM-HIGH",
  "recommendation": "ESCALATE",
  "escalationLevel": "CFO",
  "humanReviewPacket": {
    "caseId":             "CASE-DEMO-001",
    "assignedRole":       "CFO",
    "priority":           "HIGH",
    "slaMinutes":         240,
    "complianceDecision": "CLEAR",
    "fxProvider":         "JP Morgan Treasury",
    "fxSavingsUSD":       3150.0,
    "liquidityStatus":    "SUFFICIENT",
    "availableBalance":   "£4,820,000"
  },
  "auditTrail": {
    "caseId": "CASE-DEMO-001",
    "eventCount": 5,
    "events": ["FILE_UPLOADED", "PIPELINE_COMPLETE", "CASE_CREATED", "CASE_UPDATED", "CASE_DECISION"]
  }
}
```

**UiPath Studio integration pattern (HTTP Request activity):**

```
Step 1 — POST /api/upload            → upload_id
Step 2 — POST /api/process-upload    → decision + case_id
Step 3 — Branch: AUTO_EXECUTE | ESCALATE | HARD_REJECT
Step 4 — Poll GET /api/cases/{id}    → await APPROVED / REJECTED
Step 5 — GET  /api/audit?case_id=    → full compliance audit chain
```

---

## How We Built It

### Backend — Python 3.11 + FastAPI

Five deterministic Python engines, each implementing a `.run(payment: PaymentRecord) → TypedResult` interface. Determinism is deliberate: a treasury system that depends on an LLM call for every payment decision is a liability in production. Every decision is reproducible, auditable, and demo-safe with no external API key required.

FastAPI (11 REST endpoints) handles file ingestion, pipeline execution, case management, and audit queries. Two thread-safe JSON repositories (using `threading.Lock()`) provide persistence without database overhead. The SWIFT MT103 parser handles the full field set — `:20:` `:23B:` `:32A:` `:50K:` `:59:` `:70:` `:71A:`.

### Frontend — Vanilla JS SPA

Pure HTML/CSS/JavaScript served by FastAPI — no build step, no framework, no CDN dependency. Eleven pages share a sidebar, flash notification system, and dark financial theme. Key techniques: inline `COPILOT_KB` object powers the AI Copilot chat; `<animateMotion>` + `<mpath>` drives SVG routing dots on the world map; sequential `setTimeout` animates the 9-step Maestro workflow timeline.

### UiPath Integration

`src/integrations/uipath_maestro.py` implements full OAuth2 authentication against the UiPath Identity Server and the Maestro Case REST API. Flip `USE_MOCK_MAESTRO=false` and add org credentials to `.env` to switch from local case store to a real Maestro instance — no other changes required.

### Testing

84 tests across 7 suites. Engine tests cover all decision boundary conditions: compliance fuzzy match thresholds, FX rate inversions, liquidity covenant edges, risk factor combinations, and all 7 branches of the decision matrix. Web API suite uses `httpx` + FastAPI `TestClient`.

---

## Challenges We Ran Into

**Pydantic v2 attribute paths across engine outputs.** Nested model attributes (`LiquidityResult.source_position.available_balance`, `RiskResult.factors` as `list[RiskFactor]`) caused `AttributeError` failures only when the full chained pipeline ran end-to-end — not in unit tests. Required reading every model definition rather than inferring from test output.

**Server-enforced state machine.** A naive `status: any string` PATCH endpoint would allow `OPEN → APPROVED` — bypassing reviewer accountability. The `_TRANSITIONS` dict in `cases.py` maps each status to valid successors and returns HTTP 422 on invalid moves, matching Maestro's own lifecycle enforcement.

**Thread-safe JSON persistence.** Full-file rewrite on every case update under concurrent FastAPI requests required per-store `threading.Lock()` to avoid partial-write corruption — without database overhead.

**CSS variable consistency in a growing stylesheet.** The frontend defined `--card` (not `--surface`) and `--yellow` (not `--amber`). New components referencing non-existent variables rendered invisibly. Required grepping the stylesheet before writing any new UI.

---

## Accomplishments We're Proud Of

**84 tests, zero failures.** Every decision boundary is tested — not just the happy path.

**No API key required to run the demo.** `pip install -r requirements.txt && python scripts/reset_demo_data.py && uvicorn src.web.app:app --reload` — the full system is live in under 30 seconds. The LLM agentic mode (CrewAI + Claude or GPT-4o) is wired and available but never required.

**The evidence bundle.** A CFO opening CASE-DEMO-001 sees: compliance verdict with policy references, recommended FX provider with rate and savings, liquidity position with covenant status, four-factor risk breakdown, and three escalation rationale bullets — pre-organised, pre-analysed, no context-switching.

**One-second demo reset.** `python scripts/reset_demo_data.py` restores a precise known state: 3 uploads, 1 open CFO case (£2.1M, risk 71.2), 5 audit events. Essential for reliable live judging sessions.

**Complete audit chain.** Every event from file upload to case closure answers the regulator question — who, when, what decision, who approved it — with a single `GET /api/audit?case_id=CASE-DEMO-001`.

---

## What's Next

**Live UiPath Maestro API** — `src/integrations/uipath_maestro.py` is fully implemented. One env variable flip to go live.

**PDF payment extraction** — integration point is clearly documented in `processing.py`; Azure Document Intelligence or AWS Textract slots in directly.

**Real-time FX rate feeds** — replace `fx_rates.json` with Bloomberg B-PIPE or Reuters Eikon; the engine interface doesn't change.

**PostgreSQL persistence** — migrate JSON file stores to PostgreSQL / TimescaleDB for multi-instance deployment and concurrent users.

**Multi-entity consolidated liquidity** — aggregate across subsidiaries, net intercompany exposures before checking external payment headroom.

---

## Technologies Used

```
Python 3.11          FastAPI 0.115        Uvicorn 0.34
Pydantic v2 (2.12)   httpx 0.28           structlog 26.x
pytest 9.x           Click 8.x            Rich 14.x
fuzzywuzzy           python-Levenshtein   python-multipart
Vanilla JS / HTML5 / CSS3 (no build step)
UiPath Maestro Case REST API (OAuth2 — mock + live)
CrewAI + Claude (Anthropic) / GPT-4o (optional LLM mode)
```

---

## Tags

`treasury` · `payments` · `compliance` · `uipath-maestro` · `fastapi` · `python` · `fintech` · `agentic-ai` · `explainable-ai` · `human-in-the-loop` · `swift-mt103` · `fx-optimisation` · `audit-trail` · `straight-through-processing` · `stp` · `risk-management` · `uipath-agenthack-2026`

---

## Team

- **Project:** OmniTreasury AI
- **Hackathon:** UiPath AgentHack 2026
- **Submission date:** 2026-06-19

---

*OmniTreasury AI — Final Devpost Submission — UiPath AgentHack 2026*
