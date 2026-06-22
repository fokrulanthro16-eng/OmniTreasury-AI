# OmniTreasury AI — AgentHack Judging Guide

> **Competition:** UiPath AgentHack 2026
> **Team / Submitter:** fokrulanthro16-eng
> **Repository:** https://github.com/fokrulanthro16-eng/OmniTreasury-AI

---

## What This Project Does

OmniTreasury AI is an autonomous treasury payment control tower. It ingests SWIFT MT103, CSV, and JSON payment files, runs them through a 5-engine AI pipeline (compliance, FX, liquidity, risk, decision), and either:

- **Auto-executes** the payment (straight-through processing, zero human touch), or
- **Creates a UiPath Maestro Case** with a complete evidence bundle and routes it to the correct human reviewer (CFO / Treasury Manager / Compliance Officer / Legal).

The system demonstrates the full Maestro lifecycle — from robot-triggered file upload through human approval to closed case with immutable audit trail.

---

## UiPath Components Used

| Component | How It Is Used |
|---|---|
| **UiPath Orchestrator** | Package `OmniTreasury_AI` v1.0.5 deployed and executed by Robot `OmniTreasury-Robot-01`. Job verified successful in production environment. |
| **UiPath Maestro Cases** | Auto-created by the Decision Engine on every ESCALATE output. Full lifecycle managed via REST API: `OPEN → UNDER_REVIEW → APPROVED/REJECTED → CLOSED`. |
| **UiPath Studio — HTTP Request activity** | Two-step workflow: `POST /api/upload` (file ingestion) then `POST /api/process-upload/{id}` (pipeline trigger). Live run documented in README with full JSON output. |
| **UiPath Studio — Python Script activity** | Alternative integration via `main.py` → `uipath_process_payment()` for embedding OmniTreasury directly inside a Studio workflow. |
| **UiPath Robot** | `OmniTreasury-Robot-01` executes the Orchestrator job, triggers uploads, and manages the case lifecycle polling loop. |

---

## Agent Type

**Both — Coded Agents and Low-code Agents**

| Agent Type | Implementation |
|---|---|
| **Coded Agents** | Six Python agents built with the CrewAI framework: `ComplianceAuditor`, `ForexStrategist`, `LiquidityBalancer`, `RiskIntelligence`, `DecisionOrchestrator`, `DocumentIntelligence`. Defined in `src/agents/`. Agents expose a `.run()` interface and can be backed by Claude or GPT-4o (controlled via `.env`). |
| **Low-code Agents** | UiPath Studio workflows using HTTP Request activities and Python Script activities to trigger the OmniTreasury pipeline, capture decisions, and manage Maestro Cases — no Python coding required in the Studio layer. |

The deterministic engine layer (`src/engines/`) runs without any LLM API key. The CrewAI agents are an optional overlay — uncomment the `crewai` line in `requirements.txt` and add an `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` to `.env` to enable full agentic mode.

---

## Step-by-Step Setup for Judges

> **Time required:** approximately 5 minutes from git clone to live demo.
> Full instructions are also in [QUICK_START.md](QUICK_START.md).

### 1. Clone the repository

```bash
git clone https://github.com/fokrulanthro16-eng/OmniTreasury-AI.git
cd OmniTreasury-AI
```

### 2. Create a virtual environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Copy the environment file

```bash
cp .env.example .env
```

No API keys are required. The default `.env` runs entirely on mock data and local Maestro simulation.

### 5. Seed demo data

```bash
python scripts/reset_demo_data.py
```

Creates 3 demo uploads, 1 open CFO escalation case (`CASE-DEMO-001`), and 5 audit events.

### 6. Start the application

```bash
python -m uvicorn src.web.app:app --reload
```

Open **http://localhost:8000** in your browser.

### 7. Run tests (optional verification)

```bash
pytest tests/ -v
```

Expected: **84 tests passed, 0 failed**.

---

## Suggested Evaluation Path (5 minutes)

### Minute 1 — Dashboard

Open http://localhost:8000. Verify that live KPIs are populated:
- STP Rate, Open Cases, FX Savings (USD), Avg Risk Score, Total Uploads.
- These are computed from real processed data — not hardcoded.

### Minute 2 — AI Pipeline (AUTO_EXECUTE path)

Click **Upload Center** in the left nav. Click **Process** next to `sample_swift_mt103_demo.txt`.

Watch the 5-engine pipeline result expand inline:
- Compliance: CLEAR · FX: JP Morgan @ 0.9997 · Liquidity: SUFFICIENT · Risk: 23.4 LOW · Decision: **AUTO_EXECUTE**

This is the straight-through processing path — payment cleared without any human involvement.

### Minute 3 — Maestro Case Lifecycle (ESCALATE path)

Click **Cases** in the left nav. Open `CASE-DEMO-001` (£2.1M GBP, CFO assigned, risk 71.2).

- Click **Start Review** → status changes to `UNDER_REVIEW`.
- Enter reviewer notes, click **Approve** → status changes to `APPROVED`.
- The Open Cases badge in the nav drops to 0.

This demonstrates the human-in-the-loop Maestro workflow.

### Minute 4 — Audit Trail

Click **Audit Trail** in the left nav. Verify the full event chain:

```
FILE_UPLOADED → PIPELINE_COMPLETE → CASE_CREATED → CASE_UPDATED → CASE_DECISION
```

Every event shows: timestamp (UTC), actor, upload ID, case ID, description, and details payload.

### Minute 5 — AI Differentiators

Click through the five special-purpose pages:

| Page | Key Feature |
|---|---|
| **AI Copilot** | Ask: "Why was the Manchester payment escalated?" — answered from a local treasury knowledge base |
| **Explainable AI** | Animated 4-factor risk score decomposition (counterparty · operational · market · concentration) |
| **Route Intelligence** | SVG world map with animated FX routing corridors across 5 providers |
| **Maestro Workflow** | 9-step animated timeline — steps 8 and 9 are the UiPath Maestro handoff |
| **ROI Dashboard** | CFO-level business case: STP savings, FX gains, compliance cost avoidance, projections |

---

## Key Judging Criteria Addressed

| Criterion | Evidence |
|---|---|
| **UiPath Maestro integration** | Full case lifecycle (OPEN → UNDER_REVIEW → APPROVED/REJECTED → CLOSED) via REST API. Verified Orchestrator run documented in README with job output JSON. |
| **Agentic AI behavior** | 5-engine pipeline runs autonomously. Six CrewAI agents in `src/agents/`. Decisions are policy-driven and explainable. |
| **Human-in-the-loop** | Every ESCALATE output creates a Maestro Case with full evidence bundle routed to the correct approver role with SLA timer. |
| **Coded + Low-code agents** | Python CrewAI agents (coded) + UiPath Studio HTTP Request / Python Script activities (low-code). |
| **Audit and compliance** | Immutable audit trail satisfies Basel III, SOX, BSA, and FATF Recommendation 16. Queryable by case, upload, or time window. |
| **Test coverage** | 84 tests across 7 suites — all engines, parser, and API endpoints covered. |
| **Business value** | ROI Dashboard quantifies STP savings, FX gains, and compliance cost avoidance with annual projections. |

---

## Live API Verification

The following commands can be run while the app is running to verify system state:

```bash
# System health
curl http://localhost:8000/api/health

# All open cases
curl "http://localhost:8000/api/cases?status=OPEN"

# The seeded CFO escalation case
curl http://localhost:8000/api/cases/CASE-DEMO-001

# Full audit chain for that case
curl "http://localhost:8000/api/audit?case_id=CASE-DEMO-001"

# Live KPI metrics
curl http://localhost:8000/api/metrics
```

Interactive Swagger UI with all 11 endpoints: http://localhost:8000/api/docs

---

## Resetting Between Evaluations

```bash
python scripts/reset_demo_data.py
```

Restores the full demo state in under one second. Safe to run repeatedly.

---

## Repository Map for Judges

| Path | What to look at |
|---|---|
| `src/engines/` | The 5 deterministic AI engines |
| `src/agents/` | The 6 CrewAI coded agents |
| `src/integrations/uipath_maestro.py` | Maestro Case REST API integration |
| `src/web/routers/processing.py` | Pipeline orchestration + case creation logic |
| `src/web/routers/cases.py` | Case lifecycle state machine |
| `src/web/static/index.html` | Full single-page app (11 pages, dark theme) |
| `main.py` | CLI entrypoint + `uipath_process_payment()` for Studio integration |
| `tests/` | 84 tests across 7 suites |
| `ARCHITECTURE.md` | Full component and data-flow diagrams |
| `UIPATH_INTEGRATION.md` | Detailed Maestro and Studio integration guide |
| `DEMO.md` | 5-minute feature walkthrough with exact UI steps |

---

*OmniTreasury AI — UiPath AgentHack 2026 — Judging Guide*
