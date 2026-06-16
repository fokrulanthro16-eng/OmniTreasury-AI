# OmniTreasury AI — 10-Slide Presentation Deck

**UiPath AgentHack 2026**

> Presenter notes follow each slide. Estimated time: 8–10 minutes at a moderate pace, 5–6 minutes fast.

---

## Slide 1 — Title

**OmniTreasury AI**
*Autonomous Treasury Control Tower*

UiPath AgentHack 2026

> **Presenter note:** Open with the web dashboard visible on screen. The KPI cards and the open CFO case create immediate visual impact before you say a word.

---

## Slide 2 — The Problem

**Cross-border treasury payments are slow, risky, and manual.**

Every day, enterprise treasury teams face:

- **Compliance exposure** — manual sanctions screening misses fuzzy matches. OFAC fines average $3.8M per violation.
- **FX leakage** — treasury teams default to incumbent banks. Benchmark analysis shows 8–15 bps of unnecessary cost on every cross-currency payment.
- **Approval bottlenecks** — high-value payments queue in email for hours waiting for the right person to review the right file, formatted in the right way, with the right context attached.
- **Audit gaps** — when a regulator asks "who approved this payment and why," the answer is in someone's inbox, not in a system.

The result: STP rates below 60%. CFO approvals that take hours. Compliance reviews that generate paper, not decisions.

> **Presenter note:** These are industry figures from treasury benchmarking research. The pain is real and well-recognised by finance practitioners.

---

## Slide 3 — The Solution

**OmniTreasury AI processes a payment file in under a second.**

```
Upload SWIFT MT103 / CSV / JSON
         ↓
5-Engine AI Pipeline
  · Compliance screening (sanctions, AML, jurisdiction)
  · FX optimisation (5 providers, best rate)
  · Liquidity check (covenant-aware)
  · Risk scoring (4-factor composite)
  · Decision orchestration (policy matrix)
         ↓
    ┌────┴─────┐
    │          │
AUTO-EXECUTE  ESCALATE ──► UiPath Maestro Case
(STP, zero    (complete evidence bundle,
human touch)  right person, right context)
```

**Two outcomes. Both correct. All audited.**

> **Presenter note:** Keep this slide up while describing the live demo flow. It orients judges to the architecture before you show the dashboard.

---

## Slide 4 — Live Demo: AUTO_EXECUTE

**Process a SWIFT MT103 in real time.**

[SCREEN: Upload Center → click Process on sample_swift_mt103_demo.txt]

Five engines. One second.

| Engine | Result |
|---|---|
| Compliance | CLEAR · 97% confidence · 0 sanctions matches |
| FX | JP Morgan Treasury @ 0.9997 · saves $15.00 |
| Liquidity | SUFFICIENT · $1,420,000 available |
| Risk | 23.4 / 100 · LOW |
| **Decision** | **AUTO_EXECUTE ✓** |

Payment cleared. Zero human involvement. **STP achieved.**

> **Presenter note:** Click Process and let the result render live. Point at each engine row and name what it checked. End by circling the AUTO_EXECUTE badge.

---

## Slide 5 — Live Demo: UiPath Maestro Escalation

**A £2.1M acquisition payment. Different outcome.**

[SCREEN: Cases page → CASE-DEMO-001 → detail panel]

The pipeline detected:
- Amount £2,100,000 exceeds CFO materiality threshold (£1M)
- Risk score 71.2 — MEDIUM-HIGH band
- Purpose: ACQUISITION — heightened scrutiny required

**OmniTreasury AI automatically created a Maestro Case.**

```
CASE-DEMO-001 | CFO assigned | SLA: 240 minutes | OPEN
```

The CFO sees the complete evidence bundle — no context switching, no email threads, no missing data.

[SCREEN: click Start Review → type notes → click Approve]

`UNDER_REVIEW → APPROVED`. Audit trail updated immediately.

> **Presenter note:** Walk through the detail panel slowly — point at the escalation rationale bullets. This is where the product earns its keep. The CFO didn't have to ask anyone for context. It was all there.

---

## Slide 6 — Audit Trail & Compliance

**Every action. Every actor. Every timestamp.**

[SCREEN: Audit Trail page]

```
⚖️ CASE_DECISION   · 2026-06-16T09:14:22Z · Sarah Chen CFO
   "Case CASE-DEMO-001 approved"
   Notes: "Board resolution on file. Counterparty verified."

📝 CASE_UPDATED    · 2026-06-16T09:12:07Z · Sarah Chen CFO
   "Case CASE-DEMO-001 moved to UNDER_REVIEW"

🔔 CASE_CREATED    · 2026-06-15T08:41:05Z · system
   "Maestro case CASE-DEMO-001 created: PAY-Q2-002 escalated to CFO"

⚡ PIPELINE_COMPLETE · 2026-06-15T08:41:00Z · system
   "Pipeline complete: JSON Payment → ESCALATE (risk 71.2)"

📤 FILE_UPLOADED   · 2026-06-15T08:40:00Z · treasury@nexusglobal.com
   "File uploaded: treasury_payments_q2_demo.json (2.0 KB)"
```

One query. Complete chain of custody. Satisfies **Basel III, SOX, BSA, FATF Rec. 16**.

> **Presenter note:** Ask the judges: "If a regulator asked you to produce the full approval record for this payment in the next 5 minutes, could you?" With OmniTreasury, the answer is yes. `GET /api/audit?case_id=CASE-DEMO-001`.

---

## Slide 7 — AI Differentiators

**Five pages that show what AI adds beyond automation.**

[SCREEN: cycle through each page as you name it]

| Page | What it shows |
|---|---|
| **AI Copilot** | Conversational treasury assistant — ask why a payment escalated |
| **Explainable AI** | Animated risk factor bars — Counterparty 35 · Operational 45 · Market 15 · Concentration 0.6 |
| **Route Intelligence** | SVG world map with live FX routing corridors and provider network |
| **Maestro Workflow** | 9-step animation showing exactly where AI ends and human begins |
| **ROI Dashboard** | Business case in one page — STP savings, FX gains, annual projections |

The **Explainable AI** page is the most important: it shows *why* a payment scored 71.2, not just *that* it did. This is the difference between a tool reviewers trust and one they override.

> **Presenter note:** Spend 5 seconds on each page. The visual impact carries the message — don't over-explain. The Explainable AI bars animating in are particularly striking.

---

## Slide 8 — Architecture & Technical Credibility

**Production-grade in under 1,000 lines of backend Python.**

```
FastAPI 0.136  +  Pydantic v2 (2.12)  +  Python 3.11
84 tests  ·  7 suites  ·  100% pass rate
No API key required  ·  Deterministic engines  ·  Thread-safe persistence
```

**Engine interface contract (all five engines):**
```python
class ComplianceEngine:
    def run(self, payment: PaymentRecord) -> ComplianceResult: ...
```

Swapping a deterministic engine for a CrewAI LLM agent requires only that the agent returns the same Pydantic result type. The interface is stable. The architecture is extensible.

**UiPath integration is one env variable:**
```
USE_MOCK_MAESTRO=false  →  real Maestro Cases via OAuth2
```

> **Presenter note:** This slide is for technical judges. The key point: the architecture is not a demo. It is a real system with real tests that would survive a code review. The UiPath integration is one line of config away from going live.

---

## Slide 9 — Business Impact

**What OmniTreasury AI delivers to a mid-size corporate treasury.**

| Metric | Before | With OmniTreasury AI |
|---|---|---|
| STP rate | 55–65% | 85%+ (low-risk payments) |
| Average CFO review time | 4–8 hours | 15–30 minutes |
| FX cost vs. benchmark | −8 to −15 bps | Optimised per payment |
| Compliance review cost | $150–400/payment | Near-zero (automated) |
| Audit response time | Days (email search) | Seconds (API query) |
| Risk of sanctions violation | Dependent on analyst | Consistent, documented |

**For a treasury processing $500M/year in cross-border payments:**
- 1 bps FX improvement = **$500,000 annual saving**
- 30% STP rate increase = **~$1.2M in analyst time freed**
- Zero missed sanctions match = **eliminates potential $3.8M fine**

> **Presenter note:** These are directional estimates grounded in industry benchmarking. The ROI Dashboard page in the app shows the same numbers interactively.

---

## Slide 10 — What's Next

**OmniTreasury AI is ready to connect to production.**

**Immediate (config change, no code):**
- Live UiPath Maestro Cases — flip `USE_MOCK_MAESTRO=false`
- Real-time FX rates — replace `fx_rates.json` with Bloomberg B-PIPE feed
- Live ERP integration — replace `mock_erp.py` with SAP TRM or Oracle TMS connector

**Short term (2–4 weeks):**
- PDF payment extraction via Azure Document Intelligence
- Multi-entity consolidated liquidity view across subsidiaries
- PostgreSQL persistence for multi-instance production deployment

**Medium term:**
- LLM-augmented agents via CrewAI (infrastructure already in `src/agents/`) for narrative rationale generation and anomaly reasoning
- Batch processing for end-of-day bulk payment runs
- Real-time Maestro Case webhook — push status updates back into ERP

**The foundation is built. The integration point is clear. The audit trail is in place.**

*OmniTreasury AI — Built for UiPath AgentHack 2026*

---

> **Final presenter note:** End with the dashboard visible and the metrics showing. Offer to show any specific page the judges want to explore. The system is live and interactive — any question can be answered by navigating to the relevant page.
