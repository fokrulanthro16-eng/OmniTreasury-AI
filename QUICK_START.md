# OmniTreasury AI — Quick Start

> Get the system running and see a full end-to-end Maestro escalation in under 5 minutes.

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.11 or higher |
| pip | included with Python |
| Git | any recent version |

No UiPath credentials required — the demo runs entirely in local mock mode.

---

## Step 1 — Clone the repository

```bash
git clone https://github.com/fokrulanthro16-eng/OmniTreasury-AI.git
cd OmniTreasury-AI
```

---

## Step 2 — Create a virtual environment and install dependencies

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate

# Install
pip install -r requirements.txt
```

Expected output: packages install without errors. Takes ~60 seconds on first run.

---

## Step 3 — Copy the environment file

```bash
cp .env.example .env
```

The defaults in `.env.example` use mock data — no real API keys are needed for the demo.

---

## Step 4 — Seed demo data

```bash
python scripts/reset_demo_data.py
```

This creates:

| Record | ID | Content |
|---|---|---|
| Upload | `DEMO0001` | SWIFT MT103 — $50k USD — auto-executes |
| Upload | `DEMO0002` | CSV batch — 8 payments |
| Upload | `DEMO0003` | JSON portfolio — £2.1M acquisition payment |
| Case | `CASE-DEMO-001` | CFO escalation — OPEN — risk score 71.2 |
| Audit | 5 events | Full chain from FILE_UPLOADED to CASE_CREATED |

Safe to re-run at any time — resets to a clean demo state in under one second.

---

## Step 5 — Start the application

```bash
python -m uvicorn src.web.app:app --reload
```

| URL | What |
|---|---|
| http://localhost:8000 | Web dashboard (11 pages) |
| http://localhost:8000/api/docs | Interactive Swagger UI |
| http://localhost:8000/api/health | Health check endpoint |

---

## Step 6 — Verify with a quick API call

Open a second terminal (with the venv active) and run:

```bash
# Health check
curl http://localhost:8000/api/health

# Expected:
# { "status": "healthy", "version": "0.1.0", "upload_count": 3 }
```

---

## Step 7 — Run the tests (optional)

```bash
pytest tests/ -v
```

84 tests across 7 suites — all pass. Coverage targets all five engines plus the web API.

---

## What to explore next

| Goal | Where to go |
|---|---|
| See an AI pipeline run | Upload Center → click **Process** next to `sample_swift_mt103_demo.txt` |
| See a Maestro escalation | Cases → open `CASE-DEMO-001` → click **Start Review** → **Approve** |
| See the audit chain | Audit Trail page after approving the case |
| Explore all AI features | Copilot · Explainable AI · Route Intelligence · Maestro Workflow · ROI Dashboard |
| Full walkthrough | [DEMO.md](DEMO.md) |
| Judge evaluation path | [JUDGING_GUIDE.md](JUDGING_GUIDE.md) |

---

## Troubleshooting

**Port 8000 already in use**

```bash
python -m uvicorn src.web.app:app --reload --port 8080
```

**ModuleNotFoundError**

Make sure the venv is active (`(.venv)` prefix in your prompt) and dependencies are installed:

```bash
pip install -r requirements.txt
```

**Demo data missing / dashboard shows zeros**

```bash
python scripts/reset_demo_data.py
```

Then refresh the browser.

---

*OmniTreasury AI — UiPath AgentHack 2026*
