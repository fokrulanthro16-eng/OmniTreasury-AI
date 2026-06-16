# OmniTreasury AI — 5-Minute Judge Demo

> **For:** UiPath AgentHack 2026 judges
> **Duration:** ~5 minutes
> **Covers:** Every feature of the system, end-to-end

---

## Before You Start

```bash
# Step 1 — install dependencies (skip if already done)
pip install -r requirements.txt

# Step 2 — seed clean demo state
python scripts/reset_demo_data.py

# Step 3 — start the application
python -m uvicorn src.web.app:app --reload
```

Open **http://localhost:8000** in your browser.

**What the reset script creates:**

| Record | ID | Content |
|---|---|---|
| Upload 1 | `DEMO0001` | `sample_swift_mt103_demo.txt` — SWIFT MT103, $50k USD, `AUTO_EXECUTE` result |
| Upload 2 | `DEMO0002` | `batch_payments_june_demo.csv` — 8-row CSV, $1.5M total |
| Upload 3 | `DEMO0003` | `treasury_payments_q2_demo.json` — 4 payments, £2.1M GBP acquisition triggers escalation |
| Case | `CASE-DEMO-001` | £2,100,000 GBP → Manchester Industrial Holdings PLC, risk 71.2, CFO assigned, **OPEN** |
| Audit | 5 events | FILE_UPLOADED ×3, PIPELINE_COMPLETE ×1, CASE_CREATED ×1 |

---

## Step 1 — Dashboard (30 seconds)

**Page:** Dashboard (loads automatically at http://localhost:8000)

The dashboard aggregates live KPIs from the backend on every visit:

| Metric | What it proves |
|---|---|
| **STP Rate** | Percentage of payments auto-executed without human touch |
| **Open Cases** | Maestro escalations awaiting a human decision |
| **FX Savings (USD)** | Estimated savings from AI-selected FX routing vs. benchmark |
| **Avg Risk Score** | Mean composite risk across all SWIFT pipelines run |
| **Total Uploads** | File ingestion volume |

> **Judge talking point:** These are real numbers from real processing — not hardcoded. Process more files and the metrics update.

---

## Step 2 — Upload Center & AI Pipeline (60 seconds)

**Page:** Upload Center (click in left nav)

Three demo files are pre-loaded. Columns show: filename, type, size, timestamp, status, and a **Process** button.

### Run the SWIFT MT103 pipeline

Click **Process** next to `sample_swift_mt103_demo.txt` (DEMO0001).

The pipeline runs and the result expands inline. You will see output from all five engines:

```
Payment:      PAY-E01C18C5 · $50,000.00 USD · ACME MANUFACTURING INC (US)
              Reference: TXN-2026-DEMO-001 · Value date: 2026-06-17

Compliance:   CLEAR · Confidence 97%
              0 sanctions matches · 2 AML flags · 0 jurisdiction risks
              Policy ref: Bank Secrecy Act — 31 CFR 103.22

FX Route:     JP Morgan Treasury @ 0.9997
              Saves $15.00 vs. benchmark · Timing: EXECUTE NOW
              Currency pair: USD/USD

Liquidity:    SUFFICIENT
              Available: $1,420,000 · Post-payment: $1,370,000
              Covenant safe · No netting opportunity

Risk Score:   23.4 / 100 · LOW
              Counterparty 35 · Concentration 0.6 · Market 15 · Operational 45

Decision:     ✓ AUTO_EXECUTE
              Execution route: JP Morgan Treasury
              Confidence: 100%
```

> **Judge talking point:** Five engines ran in under a second. All checks passed. The Decision Engine applied the policy matrix and cleared the payment for straight-through processing — zero human involvement. This is the STP path.

---

## Step 3 — Case Management — Full Lifecycle (90 seconds)

**Page:** Cases (click in left nav)

The **Cases** badge in the nav shows **1** — one open escalation.

**CASE-DEMO-001** appears in the list:

```
Title:        PAY-Q2-002 requires CFO review — £2.1M acquisition payment
Status:       OPEN  (yellow badge)
Priority:     HIGH
Assigned:     CFO
Risk Score:   71.2
Amount:       £2,100,000 GBP
Counterparty: Manchester Industrial Holdings PLC
SLA:          240 minutes
```

Click the case card. The **detail panel** opens on the right showing:
- Payment ID, amount, currency, counterparty, value date, purpose
- Risk score with level badge
- Escalation rationale (3 bullet points explaining why CFO approval is required)
- Evidence from the pipeline: compliance decision, FX route, liquidity status, risk level

### Demonstrate the lifecycle

**Start Review** → status badge changes to `UNDER_REVIEW` (yellow). A reviewer notes field appears.

Type a reviewer note: `Acquisition due diligence complete. Board resolution on file. Counterparty verified.`

**Approve** → status badge changes to `APPROVED` (green). The Open Cases badge in the nav drops to **0**.

> **Judge talking point:** This is the human-in-the-loop decision that UiPath Maestro is built for. The AI handled intake, screening, routing, scoring, and triage. The CFO made the final call, with every relevant fact pre-organised and surfaced. Full cycle from escalation to closure is done.

---

## Step 4 — Audit Trail (45 seconds)

**Page:** Audit Trail (click in left nav)

A reverse-chronological event timeline. After the approval you just made, it shows:

| Icon | Event Type | Description |
|---|---|---|
| ⚖️ | `CASE_DECISION` | "Case CASE-DEMO-001 approved by [reviewer]" — with your notes |
| 📝 | `CASE_UPDATED` | "Case CASE-DEMO-001 moved to UNDER_REVIEW" |
| 🔔 | `CASE_CREATED` | "Maestro case CASE-DEMO-001 created: PAY-Q2-002 escalated to CFO" |
| ⚡ | `PIPELINE_COMPLETE` | "Pipeline complete: JSON Payment → ESCALATE (risk 71.2)" |
| 📤 | `FILE_UPLOADED` | "File uploaded: treasury_payments_q2_demo.json (2.0 KB)" |
| ⚡ | `PIPELINE_COMPLETE` | "Pipeline complete: SWIFT MT103 → AUTO_EXECUTE (risk 23.4)" — from Step 2 |
| 📤 | `FILE_UPLOADED` | "File uploaded: sample_swift_mt103_demo.txt (410 B)" — seeded |

Every event has: timestamp (UTC), actor, upload ID, case ID, and a details payload.

> **Judge talking point:** This is the tamper-evident audit ledger that satisfies Basel III, SOX, and treasury policy documentation requirements. Every action — system and human — is attributed and traceable. A single API call (`GET /api/audit?case_id=CASE-DEMO-001`) returns the full chain of custody for any case.

---

## Step 5 — AI Differentiators (60 seconds)

Cycle through the five pages in the left nav. Spend 10–15 seconds on each.

---

### AI Treasury Copilot

**Page:** AI Copilot

Try this question: **"Why was the Manchester Industrial Holdings payment escalated to the CFO?"**

The copilot answers from a built-in knowledge base covering: compliance rules, FX strategy, liquidity policy, risk methodology, escalation matrix, Maestro workflow, and STP metrics.

> No API key required. Runs locally. The knowledge base covers seven treasury domains.

---

### Explainable AI

**Page:** Explainable AI

Four animated factor bars show the risk score composition for an escalated payment:

| Factor | Score | What it captures |
|---|---|---|
| Counterparty | 35 | Relationship history, sanctions proximity, credit profile |
| Operational | 45 | Settlement risk, documentation completeness |
| Market | 15 | Currency volatility, geopolitical index |
| Concentration | 0.6 | Single-counterparty exposure as % of portfolio |

> **Judge talking point:** Under EU AI Act and SR 11-7 model risk management guidance, risk scores must be explainable. A reviewer who sees "71.2" without decomposition cannot make a defensible decision. These bars tell them exactly where the risk came from.

---

### Global Route Intelligence

**Page:** Route Intelligence

An animated SVG world map with continent polygons and live FX routing dots moving along payment corridors (EUR/USD, GBP/USD, SGD/USD paths). Five provider labels mark the network nodes.

> **Judge talking point:** FX routing is not a dropdown. OmniTreasury evaluates five providers in real time, ranks by effective rate + settlement speed + counterparty risk, and shows the winning route on a global map. The decision is auditable and visual.

---

### Maestro Workflow Timeline

**Page:** Maestro Workflow

A 9-step animated timeline:

```
1. Payment Intake    2. Document Intelligence   3. Compliance Screening
4. FX Analysis       5. Liquidity Check         6. Risk Scoring
7. Decision Engine   8. Maestro Case Created    9. Human Decision
```

Steps animate in sequence. Steps 8 and 9 are highlighted — this is where UiPath Maestro enters the flow.

> **Judge talking point:** The AI handles 7 of 9 steps automatically. Maestro catches the escalation (step 8). A qualified human makes the final call (step 9). This is the right division of labour for high-stakes regulated decisions.

---

### Executive ROI Dashboard

**Page:** ROI Dashboard

Six KPI cards and bar charts showing: STP automation savings, FX optimisation gains, compliance cost avoidance, average processing time reduction, headcount equivalent freed, and annual projection.

> **Judge talking point:** Every treasury deployment needs a business case. This page is the CFO's summary — concrete, measurable, tied to operations the finance team already tracks.

---

## Step 6 — API Explorer (optional, 30 seconds)

Open **http://localhost:8000/api/docs** in a new tab.

The interactive Swagger UI exposes all 11 endpoints. Try:

- `GET /api/metrics` — returns STP rate, FX savings, open case count, and average risk score in one response
- `GET /api/cases?status=OPEN` — list all open escalations
- `GET /api/audit?limit=20` — last 20 audit events

---

## Reset Between Sessions

```bash
python scripts/reset_demo_data.py
```

Restores the three canonical demo uploads, one open CFO escalation case, and five seed audit events. Takes under one second. Safe to run repeatedly.

---

## Screenshots Checklist

| # | Page | Capture |
|---|---|---|
| 1 | Dashboard | All 5 KPI cards populated |
| 2 | Upload Center | Three uploads, pipeline result expanded on DEMO0001 |
| 3 | Pipeline result | All 5 engine outputs visible, `AUTO_EXECUTE` decision |
| 4 | Cases — OPEN | CASE-DEMO-001 card + detail panel with escalation rationale |
| 5 | Cases — APPROVED | APPROVED badge, reviewer notes visible |
| 6 | Audit Trail | Full event timeline from FILE_UPLOADED through CASE_DECISION |
| 7 | AI Copilot | Chat exchange with treasury question answered |
| 8 | Explainable AI | Four animated factor bars |
| 9 | Route Intelligence | SVG map with animated routing dots |
| 10 | Maestro Workflow | 9-step timeline, steps 8–9 highlighted |
| 11 | ROI Dashboard | KPI cards and bar charts |
| 12 | Swagger UI | /api/docs endpoint list |

---

*OmniTreasury AI — Built for UiPath AgentHack 2026*
