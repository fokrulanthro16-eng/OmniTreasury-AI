# OmniTreasury AI — Demo Video Script

**UiPath AgentHack 2026**

---

## 60–90 Second Script (Primary Submission Cut)

> Use this for the Devpost video embed. Tight, judge-focused, proof-first.

### Pre-recording setup (30 seconds before hitting record)

```bash
python scripts/reset_demo_data.py
python -m uvicorn src.web.app:app --reload
```

Open browser to `http://localhost:8000`. Zoom to 125%. Have the Swagger UI open in a second tab at `http://localhost:8000/api/docs`.

---

### [0:00 – 0:08] Hook

**[SCREEN: Dashboard — KPI tiles fully loaded]**

**NARRATION:**
> "Cross-border payments touch compliance, FX, liquidity, and risk — simultaneously. OmniTreasury AI runs all four engines in under one second, then either auto-executes the payment or hands it to UiPath Maestro with the complete evidence bundle."

---

### [0:08 – 0:28] Live Pipeline — riskScore 23, REVIEW

**[SCREEN: Switch to Upload Center. Click Process on the JSON payment file.]**

**NARRATION:**
> "Watch the five-engine pipeline run."

*[Wait 1 second for result to render.]*

> "Compliance: FLAG — FATF jurisdiction match. Risk score: twenty-three. LOW. But the compliance flag overrides the auto-execute gate — so the recommendation is REVIEW."

*[Point at the result card: riskScore field, then recommendation field.]*

> "The system creates Maestro case OT-TRX12345-23 automatically — assigned to the Compliance Officer, SLA sixty minutes."

---

### [0:28 – 0:50] humanReviewPacket — Evidence Bundle

**[SCREEN: Navigate to Cases. Click OT-TRX12345-23.]**

**NARRATION:**
> "The Compliance Officer opens the case. Everything they need is here — pre-organised by the AI. Compliance flag reason. Optimal FX provider. FX savings four hundred twelve dollars. Liquidity position: sufficient. Covenant status: safe."

*[Scroll slowly through the humanReviewPacket panel.]*

> "No email threads. No spreadsheets. One screen."

**[CLICK: Approve.]**

> "Approved. The Open Cases counter drops to zero."

---

### [0:50 – 1:10] Audit Trail — caseId OT-TRX12345-23

**[SCREEN: Navigate to Audit Trail. Filter by OT-TRX12345-23.]**

**NARRATION:**
> "Five immutable events — from file upload to case decision. Who, when, what — timestamped to the second."

*[Scroll through the five events: FILE_UPLOADED → PIPELINE_COMPLETE → CASE_CREATED → CASE_UPDATED → CASE_DECISION.]*

> "Basel III, SOX, Bank Secrecy Act compliant. One API call — `GET /api/audit?case_id=OT-TRX12345-23` — returns the complete chain of custody."

---

### [1:10 – 1:25] Close

**[SCREEN: Back to Dashboard — KPIs updated.]**

**NARRATION:**
> "OmniTreasury AI. Package version one-point-zero-point-five. Verified in UiPath Orchestrator. Eighty-four tests. No API key required. One environment variable away from live Maestro Cases."

*[Hold on dashboard for 2 seconds, then fade to black.]*

---

### Recording Notes (60-90s cut)

- Keep narration cadence slow — judges read and watch simultaneously
- The 1-second pause after clicking Process is intentional — do not fill it
- Total target: 75 seconds (shoot for 70–80; 60 is rushed, 90 is the hard limit)
- Re-take trigger: run `python scripts/reset_demo_data.py` before every take

---

---

## 5-Minute Script (Full Walkthrough)

**UiPath AgentHack 2026 | Target length: 5 minutes**

---

## Pre-Recording Checklist

```bash
python scripts/reset_demo_data.py   # ← run this first, every time
python -m uvicorn src.web.app:app --reload
```

Open two browser tabs:
- Tab 1: http://localhost:8000 (dashboard)
- Tab 2: http://localhost:8000/api/docs (Swagger UI)

Zoom browser to 110%. Screen resolution: 1920×1080 or higher.
Record the full browser window including the left nav.

---

## [0:00 – 0:15] Opening — Title Card

**[SCREEN: Dashboard — KPIs visible, nav expanded]**

**NARRATION:**
> "Treasury operations sit at the intersection of compliance, capital, and risk. Every cross-border payment is a decision — and most enterprises are still making those decisions manually. OmniTreasury AI changes that."

*Pause 1 second.*

> "This is OmniTreasury AI — an autonomous treasury control tower that processes SWIFT MT103, CSV, and JSON payment files through five AI engines, then either auto-executes the payment or escalates it to a UiPath Maestro Case with the complete evidence bundle. Let me show you how it works."

---

## [0:15 – 0:45] Dashboard — Live KPIs

**[SCREEN: Dashboard, no clicking yet — let metrics load]**

**NARRATION:**
> "The dashboard shows live aggregate KPIs computed from real processing data."

*Point at each card as you name it:*

> "STP rate — the percentage of payments that cleared all checks and auto-executed without human touch."

> "Open Cases — Maestro escalations currently awaiting a human decision."

> "FX Savings — estimated USD saved by the AI's routing decisions versus the market benchmark."

> "Average Risk Score — the mean composite score across all SWIFT pipelines run."

> "These aren't hardcoded. Process more payments and the numbers update. Everything flows through the same API."

---

## [0:45 – 1:45] Upload Center — SWIFT MT103 Pipeline

**[SCREEN: click Upload Center in left nav]**

**NARRATION:**
> "The Upload Center shows our three pre-loaded demo files — a SWIFT MT103, a CSV batch, and a JSON payment portfolio."

*Pause 1 second. Let the table render fully.*

> "Let's process the SWIFT MT103."

**[CLICK: Process button next to sample_swift_mt103_demo.txt]**

*Wait for result to render — approximately 1 second.*

**NARRATION:**
> "Five engines ran in sequence. Let me walk through the result."

*Scroll through the result card slowly:*

> "Compliance — CLEAR. Ninety-seven percent confidence. Zero sanctions matches. Two AML pattern flags — below threshold. Policy reference cited."

> "FX — JP Morgan Treasury, rate 0.9997, saves fifteen dollars versus the benchmark. Timing: execute now."

> "Liquidity — SUFFICIENT. One point four million available. Post-payment balance stays well above covenant floor."

> "Risk — twenty-three point four out of one hundred. LOW classification. Counterparty thirty-five, market fifteen, operational forty-five, concentration below one."

> "Decision — AUTO_EXECUTE. Confidence one hundred percent. Payment cleared for straight-through processing. Zero human involvement required."

*Pause 1 second.*

> "That is STP. Under one second. Fully audited."

---

## [1:45 – 3:15] Case Management — Full Lifecycle

**[SCREEN: click Cases in left nav]**

**NARRATION:**
> "Now for a different scenario. The Cases page shows our open escalation."

*Let the list render. The badge in the nav shows 1.*

> "CASE-DEMO-001. A two-point-one-million-pound acquisition payment to Manchester Industrial Holdings PLC. Risk score seventy-one-point-two. Assigned to the CFO. SLA: two hundred forty minutes. Status: OPEN."

**[CLICK: the case card]**

*The detail panel opens on the right.*

**NARRATION:**
> "Click the case to open the evidence panel."

*Scroll slowly through the panel:*

> "The CFO sees: payment ID, amount, currency, counterparty, value date, and purpose. Risk score with level badge."

> "Then the escalation rationale — three bullet points explaining exactly why this payment requires CFO approval."

*Read the rationale slowly:*

> "'Payment amount exceeds CFO materiality threshold of one million pounds.' 'Purpose: ACQUISITION — additional scrutiny required per Treasury Policy.' 'Composite risk score in the MEDIUM-HIGH band.'"

> "No email threads. No attached spreadsheets. No context switching. Everything the CFO needs to make a decision is here, pre-organised by the AI."

**[CLICK: Start Review]**

*Status badge changes to UNDER_REVIEW.*

**NARRATION:**
> "The CFO opens the case for review. Status moves to UNDER_REVIEW."

**[TYPE in reviewer notes field:]**
> "Acquisition due diligence complete. Board resolution on file. Counterparty SWIFT BIC verified with correspondent bank."

**[CLICK: Approve]**

*Status badge changes to APPROVED. Nav badge drops to 0.*

**NARRATION:**
> "Approved. The Open Cases badge drops to zero. The audit trail has already been updated."

---

## [3:15 – 3:45] Audit Trail

**[SCREEN: click Audit Trail in left nav]**

**NARRATION:**
> "Every action — system and human — is recorded here with timestamp, actor, and linked IDs."

*Scroll through the timeline slowly, pausing on each event type:*

> "CASE_DECISION — your approval, the reviewer name, and the notes. Timestamped to the second in UTC."

> "CASE_UPDATED — the UNDER_REVIEW transition."

> "CASE_CREATED — when the pipeline auto-created the Maestro case."

> "PIPELINE_COMPLETE — the engine run result and risk score."

> "FILE_UPLOADED — the original file ingestion."

*Pause.*

> "One API call — `GET /api/audit?case_id=CASE-DEMO-001` — returns the complete chain of custody for this payment. Compliant with Basel III, SOX, Bank Secrecy Act, and FATF Recommendation sixteen. No email archaeology required."

---

## [3:45 – 4:45] AI Differentiators — Fast Tour

**[SCREEN: click AI Copilot]**

**NARRATION:**
> "The AI Copilot answers treasury questions from a built-in domain knowledge base."

**[TYPE: "Why was the Manchester Industrial Holdings payment escalated?"]**

*Let the response render.*

> "No API key. Runs locally. Seven treasury domains covered."

---

**[SCREEN: click Explainable AI]**

*Factor bars animate in.*

**NARRATION:**
> "The Explainable AI page shows how the risk score of seventy-one-point-two was composed. Counterparty risk, operational risk, market risk, concentration risk — each factor visible, weighted, explained. Under EU AI Act model governance requirements, this is not optional. It is the difference between a tool reviewers trust and one they bypass."

---

**[SCREEN: click Route Intelligence]**

**NARRATION:**
> "Global Route Intelligence visualises the FX routing decision — which provider, which corridor, which rate — on a live animated world map."

---

**[SCREEN: click Maestro Workflow]**

*Animation starts.*

**NARRATION:**
> "The Maestro Workflow timeline shows all nine steps. The AI handles steps one through seven. Step eight — Maestro Case creation — is where UiPath enters. Step nine is the human decision. That is the right division of labour for regulated finance."

---

**[SCREEN: click ROI Dashboard]**

**NARRATION:**
> "The ROI Dashboard gives the CFO or treasury director the business case in one page. STP savings. FX gains. Annual projections. Every number derived from real processing data."

---

## [4:45 – 5:00] Closing

**[SCREEN: back to Dashboard — KPIs now updated with the pipeline you ran]**

**NARRATION:**
> "OmniTreasury AI. Eighty-four tests. No API key required. Full audit trail. One environment variable away from live UiPath Maestro Cases."

*Pause 1 second.*

> "The complete source code, setup instructions, and five-minute judge walkthrough are in the repository. Thank you."

**[HOLD: Dashboard on screen for 3 seconds, then fade to black]**

---

## Recording Notes

**Pacing:** Speak at a deliberate, slightly slower than normal pace. Judges are reading and watching simultaneously.

**Silence:** The 1-second pauses are intentional. Do not fill them. Let the UI render.

**Mouse:** Move the mouse slowly and deliberately to each element before clicking. Fast mouse movement is hard to follow on video.

**Result rendering:** The pipeline result takes approximately 1 second to return. Do not narrate during this pause — let it breathe, then start describing the result.

**Re-takes:** If you make an error, run `python scripts/reset_demo_data.py` before re-recording any section that modified a case or ran a pipeline.

**Editing:** The natural cut points are:
- After the dashboard section (0:45)
- After the pipeline result (1:45)
- After the case approval (3:15)
- After the audit trail (3:45)
- After the AI differentiators (4:45)

---

## Alternate Shorter Cut (3-Minute Version)

If you need a 3-minute submission cut, trim as follows:

| Section | Full | Short |
|---|---|---|
| Title / problem | 0:15 | 0:10 |
| Dashboard | 0:30 | 0:15 (just name the metrics) |
| SWIFT pipeline | 1:00 | 0:45 (skip individual factor narration) |
| Case management | 1:30 | 1:00 (skip detail panel scrolling) |
| Audit trail | 0:30 | 0:15 (one scroll, no event narration) |
| AI differentiators | 1:00 | 0:30 (show 3 pages, name all 5) |
| Closing | 0:15 | 0:05 |
| **Total** | **5:00** | **3:00** |

---

*OmniTreasury AI — Demo Video Script — UiPath AgentHack 2026*
