# OmniTreasury AI — Devpost Submission

**UiPath AgentHack 2026**

---

## Headline

**OmniTreasury AI — Autonomous Treasury Control Tower with UiPath Maestro Human-in-the-Loop**

---

## Short Description (≤ 160 characters)

> AI pipeline that screens, optimises, and decides on cross-border payments — auto-executing clean ones and escalating high-risk payments to UiPath Maestro Cases for human review.

---

## What It Does

OmniTreasury AI is an autonomous treasury payment orchestration system built for enterprise finance teams that process high-volume cross-border payments.

A treasury analyst uploads a payment file — SWIFT MT103, CSV batch, or JSON portfolio — and OmniTreasury AI runs it through five parallel intelligence engines:

**1. Compliance Engine** screens the counterparty against sanctions lists using fuzzy matching (fuzzywuzzy, 75% threshold), detects AML patterns (structuring, CTR thresholds), and flags high-risk jurisdictions against FATF grey and black lists. Returns a `CLEAR`, `FLAG`, or `BLOCK` decision with confidence score and policy references.

**2. FX Engine** fetches benchmark rates for 27 currency pairs, generates quotes from five providers (JP Morgan Treasury, Deutsche Bank FX, Barclays Markets, HSBC Global FX, Citi Treasury), ranks by effective rate, and recommends execution timing — execute now, hedge, or defer based on volatility.

**3. Liquidity Engine** checks the paying entity's available cash balance against the payment amount, validates covenant headroom, and discovers netting opportunities with the counterparty that could eliminate the FX leg entirely.

**4. Risk Engine** computes a composite risk score from four dimensions: counterparty risk, concentration risk, market risk, and operational risk — producing a score from 0 to 100 with LOW / MEDIUM / HIGH / CRITICAL classification.

**5. Decision Engine** applies the policy matrix and produces one of three outcomes:
- `AUTO_EXECUTE` — all checks passed, payment proceeds straight-through with zero human involvement
- `ESCALATE` — a threshold was breached; a **UiPath Maestro Case** is auto-created and assigned to the correct approver (CFO, Treasury Manager, Compliance Officer, or Legal)
- `HARD_REJECT` — compliance block detected; payment is stopped immediately with full rationale

When a payment escalates, OmniTreasury AI creates a Maestro Case with the complete evidence bundle: compliance verdict, optimal FX route, liquidity position, four-dimension risk breakdown, and the specific rationale explaining why human review is required. The reviewer sees exactly what they need — pre-organised, pre-analysed — to make a confident decision in seconds.

The web dashboard provides:
- **Case Management** — full lifecycle (`OPEN → UNDER_REVIEW → APPROVED/REJECTED → CLOSED`) with server-enforced state machine, reviewer notes, and SLA tracking
- **Immutable Audit Trail** — every system and human action timestamped, attributed, and linked to the originating payment
- **Live KPI Dashboard** — STP rate, FX savings, open cases, average risk score, updated every 15 seconds from real processing data
- **AI Treasury Copilot** — conversational assistant with a 7-domain knowledge base (compliance, FX, liquidity, risk, escalation, Maestro workflow, STP metrics)
- **Explainable AI** — animated visual decomposition of every risk score into its four named factors, with bar charts showing weighted contributions
- **Global Route Intelligence** — animated SVG world map showing live FX routing decisions and provider network
- **Maestro Workflow Timeline** — 9-step animated orchestration from file intake to case closure, with steps 8–9 highlighting where UiPath Maestro enters
- **Executive ROI Dashboard** — STP automation savings, FX optimisation gains, compliance cost avoidance, and annual projections

---

## How We Built It

### Backend — Python 3.11 + FastAPI

The core is five deterministic Python engines, each implementing a `.run(payment)` interface returning a typed Pydantic v2 result model. Determinism was a deliberate architectural choice: a treasury system that depends on an LLM call for every payment decision is a liability in production. All intelligence is reproducible, auditable, and demo-safe with no external API key.

The `PaymentRecord` Pydantic model is the single domain entity flowing through all five engines. Each engine reads it and returns its own typed result. The `DecisionEngine` receives all four upstream results and applies the policy matrix.

A FastAPI application (11 REST endpoints) handles file ingestion, pipeline execution, case management, and audit queries. Two thread-safe JSON repositories (`data/cases.json`, `data/audit.json`) use `threading.Lock()` to prevent corruption under concurrent requests. A separate JSON-backed upload history store (`sample_data/uploads/upload_history.json`) tracks every ingested file.

The SWIFT MT103 parser handles the full field set — `:20:`, `:23B:`, `:32A:`, `:50K:`, `:59:`, `:70:`, `:71A:` — extracting payment amount, value date, currency, counterparty name, SWIFT BIC, and purpose from remittance information.

### Frontend — Vanilla JS SPA

The single-page application is pure HTML/CSS/JavaScript served by FastAPI — no build step, no framework, no CDN dependency. Eleven pages share a sidebar navigation, flash notification system, and CSS custom properties for the dark blue financial theme. Key techniques:
- `COPILOT_KB` inline object (7 topics) powers the chat engine with keyword matching
- `data-w` attribute + `setTimeout(..., 60)` triggers CSS transition on risk factor bars after DOM paint
- `<animateMotion>` + `<mpath href="#path-id">` drives SVG routing dots along world map corridors
- Sequential `setTimeout` chain animates the 9-step Maestro workflow timeline

### Demo Infrastructure

`scripts/reset_demo_data.py` seeds three canonical demo uploads, one open CFO escalation case (CASE-DEMO-001, £2.1M GBP acquisition, risk 71.2), and five seed audit events. Restoring a pristine demo state takes under one second and can be run repeatedly.

### Testing

Seven test suites, 84 tests, all passing. Engine tests are pure unit tests against synthetic payment fixtures with explicit boundary conditions. The web API suite uses `httpx` + FastAPI's `TestClient` for integration coverage across upload, processing, health, and delete endpoints.

---

## Challenges We Ran Into

**Pydantic v2 attribute paths across engine outputs.** The engine result models use nested objects, not flat dicts. `LiquidityResult.source_position.available_balance` (nested, not `.available_balance`) and `RiskResult.factors` as a `list[RiskFactor]` with `.category.value` and `.score` attributes (not a dict) caused `AttributeError` failures that only surfaced when the full pipeline ran end-to-end. Fixing them required reading the actual model definitions rather than inferring structure from API responses.

**Server-enforced state machine for case transitions.** Allowing arbitrary status updates would mean a reviewer could approve a case that was never reviewed. The `_TRANSITIONS` dict in `cases.py` maps each status to its valid successors and returns `HTTP 422` for invalid moves. Getting the UX right — disabling action buttons based on current status, refreshing the detail panel after each transition — required careful coordination between the API response and the frontend state.

**Thread-safe JSON persistence without a database.** The audit trail and cases store are written from multiple request handlers potentially concurrently. Using `threading.Lock()` per store, reading the full file before each write, and writing atomically avoids corruption without database overhead. The tradeoff — full file rewrite on every case update — is acceptable at demo scale.

**CSS variable naming consistency in an existing stylesheet.** The existing frontend defined `--card` (not `--surface`) and `--yellow` (not `--amber`). New UI components that accidentally used non-existent variables rendered invisibly against the background. Discovery required grepping the existing stylesheet rather than assuming variable names from common design systems.

---

## Accomplishments We're Proud Of

**84 tests, zero failures.** Every engine has tests covering its decision boundaries: compliance fuzzy match thresholds, FX rate inversions, liquidity covenant edges, risk factor combinations, and all seven branches of the decision matrix.

**No API key required.** The entire system runs deterministically. Every demo scenario works immediately after `pip install -r requirements.txt`. The LLM agentic mode (CrewAI + Claude or GPT-4o) is wired up and available but never required — a deliberate choice for a system that needs to be auditable and reproducible.

**The evidence bundle.** The Maestro Case payload is not a summary or a status flag. It contains the compliance decision with policy references, the recommended FX provider with rate and savings estimate, the liquidity position with covenant status, the risk breakdown by factor, and up to three escalation rationale bullet points. A CFO opening this case sees the full analysis immediately — no drilling into separate systems, no context-switching.

**One-second demo reset.** `python scripts/reset_demo_data.py` restores a precise, known state. Every demo starts from the same baseline. This matters enormously for live judging sessions and for recorded walkthroughs where reproducibility is essential.

**Complete audit chain.** From file upload to case closure, every event is logged with event type, timestamp, actor, upload ID, case ID, description, and details payload. The audit trail answers the question any regulator would ask — who uploaded this file, when did the AI run, what was the decision, who approved it, when — with a single API query.

---

## What We Learned

Treasury payment operations are governed by a web of overlapping regulatory frameworks — Bank Secrecy Act, FATF Recommendations, Basel III operational risk, SOX internal controls, SR 11-7 model risk management guidance. Building a system that a treasury team would trust means every decision must be explainable, every action must be attributed, and the system must be auditable without depending on the memory of the people who built it.

The human-in-the-loop design pattern that UiPath Maestro enables — AI handles intake, analysis, and triage; a qualified human makes the final call on high-stakes decisions — is exactly the right model for regulated finance. The AI's job is not to replace the CFO's judgement. It is to present that judgement with the best possible preparation: pre-screened, pre-analysed, pre-organised, with every relevant fact surfaced and every irrelevant distraction removed.

Explainability is not a feature — it is a prerequisite. A risk score of 71.2 is useless to a reviewer without knowing that the majority came from counterparty and operational factors. Building the `RiskFactor` list with named categories and individual scores from the start, then surfacing them in the Explainable AI page, made the system feel like a tool that augments human judgement rather than a black box that demands deference.

---

## What's Next

**Live UiPath Maestro API** — the OAuth2 integration is fully implemented in `src/integrations/uipath_maestro.py`. Flipping `USE_MOCK_MAESTRO=false` and providing org credentials connects the system to a real Maestro instance.

**PDF payment extraction** — the PDF pipeline placeholder in the processing router is ready to be replaced with Azure Document Intelligence (Form Recognizer) or AWS Textract. The integration point is clearly documented.

**Real-time FX rate feeds** — the FX engine uses a seeded `fx_rates.json` with 27 currency pairs. Replacing the data source with Bloomberg B-PIPE or Reuters Eikon is a configuration change, not an architectural one.

**Multi-entity consolidated liquidity** — extending the liquidity engine to aggregate across subsidiaries, netting intercompany exposures automatically before checking external payment headroom, is the next major feature for a global treasury function.

**PostgreSQL persistence** — migrating the JSON file stores to PostgreSQL (or TimescaleDB for the audit log) would support multi-instance deployment and concurrent users without file-level locking.

---

## Technologies Used

```
Python 3.11          FastAPI 0.136        Uvicorn 0.34
Pydantic v2 (2.12)   httpx 0.28           structlog 26.x
pytest 9.x           Click 8.x            Rich 14.x
fuzzywuzzy           python-multipart     python-Levenshtein
Vanilla JS / HTML5 / CSS3 (no build step, no framework)
UiPath Maestro Case REST API (OAuth2, mock + live)
CrewAI + Claude (Anthropic) / GPT-4o (optional LLM mode)
```

---

## Tags

`treasury` · `payments` · `compliance` · `uipath-maestro` · `fastapi` · `python` · `fintech` · `agentic-ai` · `explainable-ai` · `human-in-the-loop` · `swift-mt103` · `fx-optimisation` · `audit-trail` · `straight-through-processing` · `stp` · `risk-management`
