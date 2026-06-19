# Screenshots — OmniTreasury AI

**UiPath AgentHack 2026 — Visual Proof of Integration**

Add your screenshots to this folder before the final GitHub push.
Each file listed below corresponds to a key demo moment described in [DEMO.md](../DEMO.md)
and referenced in the main [README.md](../README.md).

---

## Required Screenshots (for Devpost submission)

| Filename | Page / Feature | What to capture |
|---|---|---|
| `01_cfo_command_center.png` | Dashboard | Full dashboard showing STP Rate, FX Savings, Open Cases, Avg Risk Score KPI tiles |
| `02_pipeline_result.png` | Upload Center | SWIFT MT103 pipeline result expanded — all 5 engines visible, `AUTO_EXECUTE` green badge |
| `03_case_detail.png` | Cases | CASE-DEMO-001 detail panel — evidence bundle, riskScore 71.2, CFO assigned, OPEN status |
| `04_audit_trail.png` | Audit | Full 5-event audit chain for CASE-DEMO-001 (FILE_UPLOADED → CASE_DECISION) |
| `05_explainable_ai.png` | Explainable AI | Animated risk factor bars — Counterparty 42, Concentration 18.5, Market 6.8, Operational 3.9 |
| `06_fx_routing_map.png` | Global Route Intelligence | SVG world map with animated routing dots and JP Morgan Treasury highlighted |
| `07_maestro_workflow.png` | Maestro Workflow Timeline | 9-step animated orchestration — steps 8–9 highlighted in UiPath gold |
| `08_case_approved.png` | Cases | CASE-DEMO-001 after CFO approval — status CLOSED, reviewer notes visible |

---

## How to Take Screenshots

### Option 1 — Use the demo seed + browser

```bash
# 1. Seed fresh demo state
python scripts/reset_demo_data.py

# 2. Start the application
python -m uvicorn src.web.app:app --reload

# 3. Open http://localhost:8000 in your browser
# 4. Use browser full-page screenshot (F12 → ... → Capture screenshot in Chrome DevTools)
```

### Option 2 — Use the pre-rendered SVG/HTML demo outputs

The `demo_output/` folder contains pre-rendered SVG and HTML versions of every dashboard page.
Open them directly in a browser and screenshot:

```
demo_output/01_cfo_command_center.html   → screenshots/01_cfo_command_center.png
demo_output/06_maestro_cases.html        → screenshots/03_case_detail.png
demo_output/07_audit_timeline.html       → screenshots/04_audit_trail.png
```

### Option 3 — Windows Snipping Tool

Press `Win + Shift + S`, select the region, paste into Paint or save directly.

---

## Screenshot Standards

- **Resolution:** minimum 1280 × 720 px, ideally 1920 × 1080
- **Format:** PNG preferred (lossless); JPG acceptable
- **Theme:** Always use the dark financial theme (default)
- **Browser:** Chrome or Edge with no extensions visible
- **File size:** Keep under 2 MB per image for GitHub display

---

## Naming Convention

```
screenshots/
├── 01_cfo_command_center.png      ← Dashboard KPIs
├── 02_pipeline_result.png         ← 5-engine output, AUTO_EXECUTE
├── 03_case_detail.png             ← Maestro Case evidence bundle
├── 04_audit_trail.png             ← Immutable audit chain
├── 05_explainable_ai.png          ← Risk factor decomposition
├── 06_fx_routing_map.png          ← Global Route Intelligence
├── 07_maestro_workflow.png        ← 9-step orchestration timeline
├── 08_case_approved.png           ← Case lifecycle complete
└── README.md                      ← This file
```

---

## After Adding Screenshots

```bash
cd OmniTreasury_AI
git add screenshots/
git commit -m "Add AgentHack demo screenshots"
git push origin main
```

The README.md screenshot table in the main repo will then render the images inline on GitHub.

---

*OmniTreasury AI — Screenshots — UiPath AgentHack 2026*
