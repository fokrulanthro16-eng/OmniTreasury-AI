# OmniTreasury AI
### Autonomous Treasury Control Tower — UiPath AgentHack 2026

> A multi-agent AI system that analyses cross-border payments for compliance, FX optimisation,
> liquidity, and risk — then either auto-executes or escalates to UiPath Maestro Case for
> human review with a complete evidence bundle.

---

## Architecture Overview

```
Payment Intake (ERP / SWIFT MT103)
         │
         ▼
  Document Intelligence Agent (parser)
         │
         ▼
  ┌──────────────────────────────────────────────────┐
  │              PARALLEL AGENT ANALYSIS              │
  │  Compliance  │  Forex      │ Liquidity  │  Risk   │
  │  Auditor     │  Strategist │ Balancer   │ Intel.  │
  └──────────────┴─────────────┴────────────┴─────────┘
         │
         ▼
  Decision Orchestrator Agent
  (applies decision matrix)
         │
    ┌────┴────┐
    │         │
AUTO-EXECUTE  ESCALATE ──► UiPath Maestro Case
    │                              │
    ▼                         Human Review
  Bank API                        │
  Audit Record              Approve / Reject
                                  │
                             Audit Closure
```

---

## Quick Start

### 1. Clone and set up environment

```bash
cd C:\Users\WALTON\OmniTreasury_AI
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### 2. Configure environment

```bash
copy .env.example .env
# Edit .env — at minimum set USE_MOCK_DATA=true (already default)
# Add ANTHROPIC_API_KEY or OPENAI_API_KEY to enable CrewAI LLM agents
```

### 3. Run demo scenarios

```bash
# Scenario 1: Clean payment → auto-approved in <30 seconds
python main.py process --scenario 1

# Scenario 2: Sanctions flag → Maestro Case created for Compliance Officer
python main.py process --scenario 2

# Scenario 3: Liquidity constraint → Maestro Case for Treasury Manager
python main.py process --scenario 3

# Scenario 4: High-value payment → CFO approval required
python main.py process --scenario 4

# Scenario 5: Netting opportunity discovered → FX transaction eliminated
python main.py process --scenario 5

# Process all 10 sample payments in batch
python main.py batch

# Parse a SWIFT MT103 file
python main.py parse-swift sample_data\swift_samples\sample_mt103.txt
```

### 4. Run tests

```bash
pytest tests/ -v
```

---

## Project Structure

```
OmniTreasury_AI/
├── main.py                         # CLI + UiPath Studio entrypoint
├── requirements.txt
├── pyproject.toml
├── .env.example
│
├── src/
│   ├── core/
│   │   ├── config.py               # Pydantic settings (all thresholds configurable)
│   │   ├── logging_config.py       # Structured logging (structlog)
│   │   └── exceptions.py           # Custom exception hierarchy
│   │
│   ├── models/                     # Pydantic v2 data models
│   │   ├── payment.py              # PaymentRecord — core domain entity
│   │   ├── compliance.py           # ComplianceResult, SanctionsMatch
│   │   ├── forex.py                # FXResult, FXRoute, RateQuote
│   │   ├── liquidity.py            # LiquidityResult, CashPosition
│   │   ├── risk.py                 # RiskResult, RiskFactor
│   │   ├── decision.py             # DecisionResult, CasePayload
│   │   └── audit.py                # AuditRecord (immutable)
│   │
│   ├── parsers/
│   │   └── swift_mt103.py          # Full SWIFT MT103 parser
│   │
│   ├── engines/                    # Deterministic business logic
│   │   ├── compliance_engine.py    # Sanctions screening, AML, jurisdiction
│   │   ├── forex_engine.py         # Multi-provider rate comparison, routing
│   │   ├── liquidity_engine.py     # Cash position check, netting discovery
│   │   ├── risk_engine.py          # 4-dimension composite risk scoring
│   │   └── decision_engine.py      # Decision matrix application
│   │
│   ├── agents/                     # CrewAI agent definitions
│   │   ├── base_agent.py           # Abstract base + LLM builder
│   │   ├── compliance_auditor.py   # Compliance Auditor Agent
│   │   ├── forex_strategist.py     # Forex Strategist Agent
│   │   ├── liquidity_balancer.py   # Liquidity Balancer Agent
│   │   ├── risk_intelligence.py    # Risk Intelligence Agent
│   │   ├── decision_orchestrator.py # Decision Orchestrator (coordinates all)
│   │   └── document_intelligence.py # Document Intelligence Agent
│   │
│   ├── integrations/
│   │   ├── uipath_maestro.py       # Maestro Case API (mock + live)
│   │   ├── mock_erp.py             # Simulates SAP TRM payment feed
│   │   ├── mock_fx_feed.py         # Simulates Bloomberg/Reuters rates
│   │   └── mock_banking_api.py     # Simulates bank payment submission
│   │
│   └── utils/
│       ├── audit_trail.py          # Append-only audit ledger
│       └── helpers.py              # Rich terminal display helpers
│
├── tests/
│   ├── test_compliance_engine.py   # 15 test cases
│   ├── test_forex_engine.py        # 10 test cases
│   ├── test_liquidity_engine.py    # 11 test cases
│   ├── test_risk_engine.py         # 12 test cases
│   ├── test_decision_engine.py     # 13 test cases
│   └── test_swift_parser.py        # 12 test cases
│
└── sample_data/
    ├── payments.json               # 10 synthetic payment scenarios
    ├── sanctions_list.json         # 8 synthetic OFAC/UN entries
    ├── fx_rates.json               # 27 currency pairs with volatility/trend
    ├── liquidity_positions.json    # 8 entity accounts + netting + funding
    ├── entity_register.json        # 5 corporate entities + approved counterparties
    ├── risk_thresholds.json        # Configurable limit framework
    └── swift_samples/
        └── sample_mt103.txt        # Full MT103 demo message
```

---

## Decision Matrix

| Compliance | Risk Score | Liquidity | Amount | Decision |
|---|---|---|---|---|
| CLEAR | < 60 | SUFFICIENT | < $1M | AUTO_EXECUTE |
| CLEAR | 60–79 | Any | Any | ESCALATE → Treasury Manager |
| CLEAR | ≥ 80 | Any | Any | ESCALATE → Treasury Manager |
| CLEAR | Any | INSUFFICIENT | Any | ESCALATE → Treasury Manager |
| CLEAR | < 60 | OK | ≥ $1M | ESCALATE → CFO |
| FLAG | Any | Any | Any | ESCALATE → Compliance Officer |
| BLOCK | Any | Any | Any | HARD_REJECT |

---

## UiPath Studio Integration

### Python Script Activity (simple)

```python
# In UiPath Studio Python Script activity:
import sys
sys.path.insert(0, r"C:\Users\WALTON\OmniTreasury_AI")
from main import uipath_process_payment

result_json = uipath_process_payment("PAY-2026-0002")
# result_json is a JSON string with: decision, escalation_level, case_payload
```

### Maestro Case (live mode)

Set in `.env`:
```
USE_MOCK_MAESTRO=false
UIPATH_ORG_ID=your_org_id
UIPATH_TENANT_NAME=your_tenant
UIPATH_CLIENT_ID=your_client_id
UIPATH_CLIENT_SECRET=your_client_secret
```

The system will authenticate via OAuth2 and create real Maestro Cases on escalation.

---

## Agent Modes

### Engine Mode (default, no API key required)
All agents run their underlying business engines deterministically. Fast, predictable, demo-safe.

### CrewAI Agentic Mode (requires API key)
Add `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` to `.env`. Call:

```python
orchestrator = DecisionOrchestratorAgent()
result = orchestrator.run_crew(payment)  # LLM-augmented reasoning
```

---

## Configuration

All thresholds are configurable via `.env` without code changes:

| Variable | Default | Description |
|---|---|---|
| `AUTO_APPROVE_MAX_AMOUNT` | 500000 | Max amount for auto-approval |
| `RISK_ESCALATION_THRESHOLD` | 60 | Risk score triggering escalation |
| `HIGH_RISK_THRESHOLD` | 80 | Risk score for high-risk classification |
| `COMPLIANCE_FUZZY_MATCH_THRESHOLD` | 75 | Sanctions name matching sensitivity |
| `MATERIALITY_THRESHOLD` | 1000000 | CFO approval threshold |
| `USE_MOCK_DATA` | true | Use sample_data instead of live ERP |
| `USE_MOCK_MAESTRO` | true | Simulate Maestro Cases in-memory |

---

## Demo Scenarios Quick Reference

| # | Scenario | Expected Decision | Key Feature Shown |
|---|---|---|---|
| 1 | Clean EUR payment | AUTO_EXECUTE | FX optimisation, speed |
| 2 | Sanctions fuzzy match | ESCALATE (Compliance Officer) | Maestro Case creation |
| 3 | Liquidity constrained | ESCALATE (Treasury Manager) | Covenant protection |
| 4 | High-value GBP | ESCALATE (CFO) | Materiality threshold |
| 5 | Netting opportunity | NETTING_AVAILABLE | FX elimination |
| 6 | Exact SDN match | HARD_REJECT | Compliance blocking |

---

## Technical Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Data Models | Pydantic v2 |
| Agent Framework | CrewAI 0.28+ |
| LLM | Claude (Anthropic) / GPT-4o (OpenAI) |
| HTTP Client | httpx |
| Logging | structlog |
| CLI | Click + Rich |
| Testing | pytest + pytest-cov |
| UiPath Integration | Maestro Case REST API / OAuth2 |

---

*OmniTreasury AI — Built for UiPath AgentHack 2026*
