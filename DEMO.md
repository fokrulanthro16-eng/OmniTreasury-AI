# OmniTreasury AI — 5-Minute Judge Walkthrough

> **Target audience:** UiPath AgentHack 2026 judges
> **Time required:** ~5 minutes
> **What you'll see:** Every key feature of the system working end-to-end

---

## Setup (30 seconds)

```bash
# 1. Install dependencies (skip if already done)
pip install -r requirements.txt

# 2. Reset to clean demo state
python scripts/reset_demo_data.py

# 3. Start the web app
python -m uvicorn src.web.app:app --reload
```

Open **http://localhost:8000** in your browser.

---

## Step 1 — Dashboard (30 seconds)

You land on the **Dashboard**. Notice:

- **STP Rate** — what percentage of payments were auto-approved without human touch
- **Open Cases** — escalations waiting for CFO/Treasury/Compliance review
- **FX Savings** — estimated USD savings from AI-selected FX routing
- **Avg Risk Score** — composite risk across all processed payments

These metrics update live from the backend every 15 seconds.

---

## Step 2 — Upload a SWIFT payment (30 seconds)

Click **Upload Center** in the left nav.

- The three demo files are already shown: a SWIFT MT103, a CSV batch, and a JSON portfolio.
- Click **Process** next to `sample_swift_mt103_demo.txt` (DEMO0001).

Watch OmniTreasury run the full **5-engine pipeline in real time**:
1. SWIFT MT103 parser extracts payment fields
2. Compliance engine screens sanctions + AML
3. FX engine finds the best rate across 5 providers
4. Liquidity engine checks covenant headroom
5. Decision engine applies the policy matrix

**Result:** `AUTO_EXECUTE` — payment cleared, no human needed. STP achieved.

---

## Step 3 — Case Management (90 seconds)

Click **Cases** in the left nav.

**CASE-DEMO-001** is already open — a £2,100,000 GBP acquisition payment that triggered CFO escalation because it exceeded the materiality threshold (£1M).

Click the case card to open the detail panel. You'll see:
- **Payment ID / Amount / Currency / Counterparty**
- **Risk score** (71.2 — MEDIUM-HIGH band)
- **Escalation rationale** (why CFO approval is required)
- **SLA** (240 minutes remaining)

**To demonstrate the full lifecycle:**

1. Click **Start Review** → case moves to `UNDER_REVIEW`
2. Type a reviewer note (e.g., `Verified acquisition documentation. Board approval obtained.`)
3. Click **Approve** → case moves to `APPROVED`

The status badge updates immediately. Open Cases badge in the nav drops to 0.

---

## Step 4 — Audit Trail (60 seconds)

Click **Audit Trail** in the left nav.

Every system action is recorded with timestamp, actor, and context:

| Event | What it shows |
|---|---|
| `CASE_DECISION` | Your approve/reject with reviewer name |
| `CASE_UPDATED` | Status transition (OPEN → UNDER_REVIEW → APPROVED) |
| `CASE_CREATED` | Auto-creation when pipeline detected escalation |
| `PIPELINE_COMPLETE` | Engine run result + decision |
| `FILE_UPLOADED` | File ingestion with size and type |

This is the **complete, tamper-evident evidence bundle** — every action traceable back to a payment.

---

## Step 5 — AI Differentiators (60 seconds)

Use the left nav to explore the five AI differentiation features:

### AI Treasury Copilot
Click **AI Copilot**. Ask it: *"Why was this payment escalated to the CFO?"*
The copilot answers from a built-in treasury knowledge base covering compliance rules, FX strategy, liquidity management, risk scoring, decision policy, Maestro workflow, and STP metrics.

### Explainable AI
Click **Explainable AI**. See the four risk factor bars (Counterparty, Concentration, Market, Operational) that compose the 71.2 risk score — with visual weights so reviewers understand *why* a payment was escalated, not just *that* it was.

### Global Route Intelligence
Click **Route Intelligence**. Animated SVG world map shows the live FX routing network — which bank/provider OmniTreasury selected and why (best rate, fastest settlement, lowest counterparty risk).

### Maestro Workflow
Click **Maestro Workflow**. See the 9-step orchestration timeline — from file ingestion through parallel engine analysis to Maestro case creation and human decision — animated step-by-step.

### Executive ROI Dashboard
Click **ROI Dashboard**. See the business case: STP automation savings, FX optimisation gains, compliance cost avoidance, and annual projection — everything a CFO or treasury director needs to justify deployment.

---

## Step 6 — Reset and Repeat (optional)

```bash
python scripts/reset_demo_data.py
```

Wipes all runtime data and restores the three canonical demo uploads + one open case. Takes <1 second.

---

## API Explorer

All data is available as REST JSON:

```
GET  /api/health          — system status
GET  /api/uploads         — all upload records
POST /api/upload          — submit a new file
POST /api/process-upload/{id} — run the AI pipeline
GET  /api/cases           — all Maestro cases
GET  /api/cases?status=OPEN   — filter by status
PATCH /api/cases/{id}     — approve / reject / review
GET  /api/audit           — full immutable audit trail
GET  /api/metrics         — live aggregate KPIs
GET  /api/docs            — interactive Swagger UI
```

---

*OmniTreasury AI — Built for UiPath AgentHack 2026*
