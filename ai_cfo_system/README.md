# AI CFO System — Multi-Agent Financial Intelligence Platform

> **Zero-hallucination financial analysis for CFOs, Controllers, and FP&A teams.**  
> Built on deterministic math engines, GAAP/IFRS compliance automation, and LangGraph multi-agent orchestration. Every number is exact. No LLM generates financial figures.

---

## Table of Contents

1. [Goal](#1-goal)
2. [How It Works — Architecture](#2-how-it-works--architecture)
3. [Agent Roster](#3-agent-roster)
4. [Dashboard Suite](#4-dashboard-suite)
5. [How to Use It](#5-how-to-use-it)
6. [Company Datasets](#6-company-datasets)
7. [GAAP & IFRS Standards Enforced](#7-gaap--ifrs-standards-enforced)
8. [AI Tools Used to Build It](#8-ai-tools-used-to-build-it)
9. [Debugging Sheet](#9-debugging-sheet)
10. [Project Structure](#10-project-structure)

---

## 1. Goal

The **AI CFO System** is a production-grade multi-agent financial intelligence platform designed to assist Chief Financial Officers, Controllers, and FP&A analysts with:

| Capability | Detail |
|---|---|
| **Automated KPI computation** | 17 exact financial KPIs from raw accounting data |
| **GAAP compliance audit** | 12 ASC standards checked deterministically |
| **IFRS compliance audit** | 12 IASB standards checked deterministically |
| **Budget vs Actuals** | SAB 99 materiality flagging (≥5% threshold) |
| **Revenue forecasting** | Linear Regression + Holt-Winters ensemble (40/60) |
| **Anomaly detection** | IQR statistical method, no ML model needed |
| **Cash runway** | Burn rate + runway months from cash flow data |
| **AI debate** | GAAP agent vs IFRS agent structured debate via LLM |
| **CFO dashboards** | 4 HTML dashboards per company, browser-native |
| **Agent analysis** | 8 deterministic findings per dashboard, zero LLM |

**Why zero-LLM math?** LLMs hallucinate numbers. A CFO cannot present a board with a gross margin figure that was "estimated" by a language model. Every metric in this system is computed by Pandas/NumPy arithmetic from source data — the LLM is only used for narrative interpretation and structured debate, never for calculation.

---

## 2. How It Works — Architecture

The system is built on a **4-layer anti-hallucination architecture**:

```
┌──────────────────────────────────────────────────────────────────┐
│  LAYER 1 — Deterministic Math Engine                             │
│  Pandas · NumPy · Scikit-learn · Statsmodels                     │
│  All KPIs, variances, forecasts, anomalies computed exactly.     │
│  Zero rounding errors. Reproducible to the cent.                 │
└─────────────────────────┬────────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────────┐
│  LAYER 2 — Pydantic v2 Schema Validation                         │
│  AnalysisOutput · FinancialData schemas                          │
│  Rejects any output that doesn't match the declared structure.   │
│  min_length / max_length enforced on all list fields.            │
└─────────────────────────┬────────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────────┐
│  LAYER 3 — Secure Local Infrastructure                           │
│  FastAPI · SQLAlchemy · SQLite (local) · SHA-256 ledger hashes   │
│  100% local — no financial data leaves the machine.              │
│  IRS $75 Rule · $31M UNICAP threshold enforced.                  │
└─────────────────────────┬────────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────────┐
│  LAYER 4 — RAG Knowledge Retrieval                               │
│  Sentence-Transformers · pgvector (SQLite fallback)              │
│  Standards documents retrieved and cited in agent analysis.      │
│  Prevents LLM from fabricating regulatory citations.             │
└──────────────────────────────────────────────────────────────────┘
```

### Pipeline Flow

```
Raw Financial Data (dict)
        │
        ▼
[Supervisor Agent] ─── orchestrates all agents via LangGraph
        │
        ├──▶ [Data Agent]       validates & normalises input data
        ├──▶ [Math Engine]      computes all 17 KPIs, variance, forecast, runway
        ├──▶ [GAAP Agent]       checks 12 ASC standards
        ├──▶ [IFRS Agent]       checks 12 IASB standards
        ├──▶ [RAG Agent]        retrieves relevant regulatory context
        ├──▶ [Analysis Agent]   structures LLM narrative (optional)
        ├──▶ [Debate Agent]     GAAP vs IFRS structured debate (optional)
        └──▶ [HITL Node]        flags anomalies for human-in-the-loop review
                │
                ▼
        [Dashboard Generator]
        4 HTML files per company — CFO · Cost · Headcount · Inventory
        Each with deterministic AI Agent Analysis (zero LLM)
```

### LangGraph State Machine

The orchestration uses **LangGraph** with a typed `CFOAgentState` object passed between nodes. Each agent reads from and writes to the shared state dictionary. The supervisor routes based on completion flags, not LLM decisions.

---

## 3. Agent Roster

| Agent | File | Role | LLM? |
|---|---|---|---|
| **Supervisor** | `backend/agents/supervisor.py` | Routes state between agents | No |
| **Data Agent** | `backend/agents/data_agent.py` | Validates and normalises input | No |
| **Math Engine** | `backend/agents/math_engine.py` | Computes all KPIs, variance, forecast | **No** |
| **GAAP Agent** | `backend/agents/gaap_agent.py` | Calls GAAP compliance engine | No |
| **IFRS Agent** | `backend/agents/ifrs_agent.py` | Calls IFRS compliance engine | No |
| **RAG Agent** | `backend/agents/rag_agent.py` | Retrieves regulatory context | No |
| **Analysis Agent** | `backend/agents/analysis_agent.py` | LLM narrative summary | **Yes** |
| **Debate Agent** | `backend/agents/debate_agent.py` | GAAP vs IFRS LLM debate | **Yes** |
| **HITL Node** | `backend/agents/human_loop_node.py` | Human-in-the-loop approval gate | No |
| **Reporting Agent** | `backend/agents/reporting_agent.py` | Assembles final output | No |

**GAAP Engine** (`backend/compliance/gaap_engine.py`) — 12 checks:
`ASC 205-40` Going Concern · `ASC 230` Cash Flows · `ASC 260` EPS · `ASC 280` Segments · `ASC 310/326` CECL · `ASC 350` Goodwill · `ASC 450` Contingencies · `ASC 606` Revenue · `ASC 740` Income Taxes · `ASC 820` Fair Value · `ASC 842` Leases · `SAB 99` Materiality

**IFRS Engine** (`backend/compliance/ifrs_engine.py`) — 12 checks:
`IAS 1` Presentation · `IAS 2` Inventories · `IAS 7` Cash Flows · `IAS 12` Income Taxes · `IAS 16` PPE · `IAS 33` EPS · `IAS 36` Impairment · `IAS 37` Provisions · `IAS 38` Intangibles · `IFRS 9` ECL · `IFRS 15` Revenue · `IFRS 16` Leases

---

## 4. Dashboard Suite

Four HTML dashboards are generated per company, written to `data/{company}/`:

### AI CFO Dashboard (`ai_cfo_dashboard.html`)
- 8 KPI cards: Revenue, Gross Margin, EBITDA, Net Income, Cash, Current Ratio, Net Debt, ROE
- Revenue bar chart: historical quarters + 8Q forecast (LR 40% + Holt-Winters 60%)
- Revenue segment donut chart (ASC 280)
- Budget vs Actuals variance table with SAB 99 materiality flags
- GAAP 12/12 compliance table
- IFRS 12/12 compliance table
- RAG retrieved knowledge panel
- **AI Agent Analysis**: 8 deterministic findings — gross margin, EBITDA, liquidity, revenue variance, DSO, interest coverage, GAAP issues, runway

### Monthly Cost Analysis Dashboard (`cost_dashboard.html`)
- 4 KPI cards: Total OpEx, OpEx % Revenue, Cost per Employee, Gross Margin
- 6-month stacked cost trend (COGS / SG&A / R&D)
- Cost mix donut chart
- Cost efficiency benchmark table
- Budget vs Actual cost categories
- **AI Agent Analysis**: 8 findings — gross margin, R&D %, SG&A %, budget variances, FCF, cost per employee, EBITDA

### Headcount KPI Dashboard (`headcount_dashboard.html`)
- 4 KPI cards: Total HC, Revenue/Employee, Cost/Employee, Profit/Employee
- 6-month headcount trend bar chart
- Department breakdown donut
- Hiring & attrition table
- Department cost/productivity table
- **AI Agent Analysis**: 8 findings — revenue/employee, profit/employee, engineering ratio, all-in cost, NRR, HC growth, R&D/engineer, SG&A/sales

### Inventory Monitoring Dashboard (`inventory_dashboard.html`)
- 4 KPI cards: Inventory (FIFO), Turnover, DIO, % of COGS
- 6-month inventory trend
- Category breakdown donut (ASC 330 / IAS 2)
- Inventory aging table (0–30, 31–60, 61–90, 90+ days)
- SKU reorder status table
- **AI Agent Analysis**: 8 findings — FIFO compliance, turnover, DIO, materiality, aging, AP coverage, NRV assessment

All findings cite specific ASC/IAS standards. Each finding card shows severity (`ok` / `warn` / `critical` / `info`) and source tag (`Math Engine` / `GAAP Engine` / `IFRS Engine`).

---

## 5. How to Use It

### Prerequisites

- Python 3.10+
- Windows / macOS / Linux
- (Optional) Anthropic API key — system falls back to Ollama if absent
- (Optional) Ollama with `llama3.2:1b` or `llama3:8b` — only needed for LLM narrative/debate

### Installation

```bash
git clone https://github.com/moussdiop240-source/ai-cfo-system.git
cd ai-cfo-system/ai_cfo_system
pip install -r requirements.txt
```

### Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```env
ANTHROPIC_API_KEY=sk-ant-api03-...   # optional — leave blank to use Ollama
OLLAMA_MODEL=llama3.2:1b             # or llama3:8b if you have GPU
OLLAMA_BASE_URL=http://localhost:11434
```

### Run the Streamlit UI

```bash
streamlit run streamlit_app.py
```

Opens at `http://localhost:8501`.

### Streamlit Workflow

```
Sidebar
  1. Select Company Dataset  ←  NovaTech / Meridian / Horizon / Custom
  2. Select LLM Backend      ←  Anthropic API or Ollama (local)
  3. ▶ Run Deterministic Pipeline   ←  computes all KPIs, GAAP, IFRS
  4. Run AI Analysis (optional)     ←  LLM narrative (slow on CPU)
  5. Run GAAP/IFRS Debate (optional)←  structured LLM debate
  6. 📊 Generate All Dashboards     ←  writes 4 HTML files & opens browser
```

### Generate Dashboards via Script (All 3 Companies)

```bash
cd ai_cfo_system
python - << 'EOF'
import sys, os
sys.path.insert(0, ".")
import dashboards.html_generators as _gen
from data.sample_companies import COMPANIES
from backend.agents.math_engine import FinancialCalculationEngine
from backend.compliance.gaap_engine import GAAPEngine
from backend.compliance.ifrs_engine import IFRSEngine

math_eng = FinancialCalculationEngine()
gaap_eng = GAAPEngine()
ifrs_eng = IFRSEngine()

ACTUALS_KEYS = ["revenue","cogs","gross_profit","ebitda","ebit","net_income",
    "rd_expense","sg_a_expense","operating_expenses","interest_expense",
    "tax_provision","capex","free_cash_flow","depreciation_amortization"]

rag_chunks = [
    {"title": "ASC 606", "content": "Revenue recognised when performance obligations are satisfied."},
    {"title": "ASC 842", "content": "Lessees recognise right-of-use asset and lease liability."},
    {"title": "IAS 36",  "content": "Assets tested for impairment when indicators exist."},
    {"title": "SAB 99",  "content": "Items material if a reasonable investor would consider them important."},
]

for key, data in COMPANIES.items():
    co_dir = os.path.join("data", key)
    os.makedirs(co_dir, exist_ok=True)
    actuals  = {k: float(data[k]) for k in ACTUALS_KEYS if k in data}
    kpis     = math_eng.calculate_kpis(data)
    variance = math_eng.calculate_variance_analysis(actuals, data.get("budget", {}))
    anomalies= math_eng.detect_anomalies(data, kpis)
    runway   = math_eng.calculate_cash_runway(data, kpis)
    forecast = math_eng.forecast_revenue(data.get("historical_revenue", []), 8)
    gaap     = gaap_eng.check_all(data, kpis, variance, runway)
    ifrs     = ifrs_eng.check_all(data, kpis, variance, runway)
    name, period = data["_meta"]["name"], data["_meta"]["period"]
    orig = _gen._ROOT
    _gen._ROOT = os.path.abspath(co_dir)
    _gen.generate_cfo_dashboard(data, kpis, variance, gaap, ifrs, forecast, runway, anomalies, rag_chunks, name, period)
    _gen.generate_cost_dashboard(data, kpis, name, period)
    _gen.generate_headcount_dashboard(data, kpis, name, period)
    _gen.generate_inventory_dashboard(data, kpis, name, period)
    _gen._ROOT = orig
    print(f"  {name}: 4 dashboards → data/{key}/")
EOF
```

### Run FastAPI Backend (optional)

```bash
cd ai_cfo_system
uvicorn backend.main:app --reload --port 8000
```

API docs at `http://localhost:8000/docs`

### Run Tests

```bash
cd ai_cfo_system
pytest tests/ -v
```

---

## 6. Company Datasets

Three pre-built company datasets are included in `data/sample_companies.py`:

| Key | Company | Sector | Period | Revenue | GM | EBITDA |
|---|---|---|---|---|---|---|
| `novatech` | NovaTech Solutions Inc. | SaaS | Q1 2026 | $12.84M | 72.0% | 24.4% |
| `meridian` | Meridian Manufacturing Co. | Industrial | Q1 2026 | $28.40M | 30.0% | 12.0% |
| `horizon` | Horizon Community Foundation | Non-Profit 501(c)(3) | FY 2025 | $6.24M | 80.0% | 20.0% |

Each dataset includes: full income statement, balance sheet, cash flow statement, segment breakdown, budget vs actuals, 8–9 quarters of historical revenue, GAAP/IFRS policy flags, lease data, goodwill, credit loss provisions.

### Adding a Custom Company

Add a new entry to `data/sample_companies.py` following the same schema, then register it:

```python
COMPANIES["mycompany"] = MY_COMPANY_DATA
```

Minimum required fields:
```python
{
    "_meta": {"name": "Company Name", "sector": "SaaS", "period": "Q1 2026"},
    "revenue": 10_000_000,
    "cogs": 3_000_000,
    "gross_profit": 7_000_000,
    "ebitda": 2_000_000,
    "net_income": 1_200_000,
    "cash": 5_000_000,
    "current_assets": 8_000_000,
    "current_liabilities": 3_000_000,
    "total_assets": 20_000_000,
    "total_equity": 12_000_000,
    "budget": {"revenue": 9_500_000, "cogs": 3_200_000},
    "historical_revenue": [7.2e6, 7.8e6, 8.4e6, 9.1e6, 9.8e6, 10.0e6],
}
```

---

## 7. GAAP & IFRS Standards Enforced

### GAAP (ASC — 2026)

| Standard | Check | Key Threshold |
|---|---|---|
| ASC 205-40 | Going Concern | Cash runway < 12 months → disclosure required |
| ASC 230 | Cash Flows | Operating / investing / financing classification |
| ASC 260 | EPS | Basic and diluted EPS computed |
| ASC 280 | Segments | Revenue segments disclosed (≥10% rule) |
| ASC 310/326 | CECL Credit Losses | Allowance vs DSO, ECL model required |
| ASC 350 | Goodwill | Annual impairment test flag |
| ASC 450 | Contingencies | Probable loss accrual |
| ASC 606 | Revenue Recognition | Performance obligations, contract liability |
| ASC 740 | Income Taxes | Effective tax rate, deferred tax |
| ASC 820 | Fair Value | Level 1/2/3 hierarchy |
| ASC 842 | Leases | ROU asset + lease liability recognition |
| SAB 99 | Materiality | 5% threshold — items above flagged as Material |

### IFRS (IASB — 2026)

| Standard | Check | Key Difference from GAAP |
|---|---|---|
| IAS 1 | Presentation | Statement of comprehensive income required |
| IAS 2 | Inventories | **LIFO strictly prohibited** — FIFO or weighted avg only |
| IAS 7 | Cash Flows | Direct or indirect method |
| IAS 12 | Income Taxes | Deferred tax on all temporary differences |
| IAS 16 | PPE | Revaluation model allowed (vs cost only under GAAP) |
| IAS 33 | EPS | Same as ASC 260 |
| IAS 36 | Impairment | CGU recoverable amount; reversals allowed |
| IAS 37 | Provisions | Constructive obligations included |
| IAS 38 | Intangibles | Development costs capitalised if criteria met |
| IFRS 9 | ECL | Expected credit loss 3-stage model |
| IFRS 15 | Revenue | Same 5-step model as ASC 606 |
| IFRS 16 | Leases | No operating lease exemption (unlike ASC 842) |

---

## 8. AI Tools Used to Build It

### Claude Code (Anthropic)
The entire system was designed, architected, debugged, and iterated using **Claude Code** — Anthropic's AI coding agent running in the terminal. Claude Code was used to:
- Architect the 4-layer anti-hallucination system
- Write all Python modules (agents, engines, generators, schemas)
- Fix runtime errors (Pydantic v2 deprecations, SQLAlchemy reserved names, Python 3.11 f-string backslash limitation)
- Design the professional CFO dashboard CSS and HTML layout
- Write the deterministic AI agent analysis engine (zero LLM, rule-based findings)
- Debug all 3 company datasets and ensure deterministic pipeline outputs

### Claude Sonnet 4.6 (claude-sonnet-4-6)
The underlying model powering the Claude Code agent for this project. Also used as the optional LLM backend for the AI Analysis and GAAP/IFRS Debate features.

### Anthropic API
Used as the primary LLM backend for the Analysis Agent and Debate Agent when an API key is configured. Structured outputs via the `instructor` library ensure Pydantic schema compliance.

### Ollama (Local LLM Fallback)
Used as a 100% local, offline LLM backend when no Anthropic API key is available. Tested with:
- `llama3.2:1b` — fast, CPU-compatible (recommended for CPU-only machines)
- `llama3:8b` — higher quality, requires GPU or significant patience on CPU

### LangGraph
Multi-agent orchestration framework. Provides typed state machines, node routing, and conditional edges between agents. The `CFOAgentState` TypedDict is the shared memory bus between all agents.

### Key Python Libraries

| Library | Version | Role |
|---|---|---|
| `pandas` | 2.2.3 | All financial arithmetic — zero approximation |
| `numpy` | 1.26.4 | Statistical calculations, IQR anomaly detection |
| `scikit-learn` | 1.5.2 | Linear Regression for revenue forecasting |
| `statsmodels` | 0.14.4 | Holt-Winters exponential smoothing |
| `pydantic` | v2.x | Schema validation — Layer 2 of anti-hallucination |
| `fastapi` | 0.115+ | REST API backend |
| `streamlit` | 1.35+ | Interactive UI |
| `sentence-transformers` | 3.3.1 | RAG embedding layer |
| `anthropic` | 0.40+ | Anthropic API client |
| `instructor` | 1.7+ | Structured LLM outputs with Pydantic |
| `langgraph` | 0.2.55 | Multi-agent state machine |

---

## 9. Debugging Sheet

### Installation Issues

| Error | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'anthropic'` | Package not installed | `pip install anthropic fastapi uvicorn[standard] instructor python-multipart httpx` |
| `ModuleNotFoundError: No module named 'langgraph'` | Missing package | `pip install langgraph langchain` |
| `ModuleNotFoundError: No module named 'statsmodels'` | Missing package | `pip install statsmodels` |
| `ModuleNotFoundError: No module named 'sentence_transformers'` | Missing package | `pip install sentence-transformers` |
| `pip install` hangs | Network / firewall | Use `pip install --timeout 120 -r requirements.txt` |

### Pydantic Errors

| Error | Cause | Fix |
|---|---|---|
| `PydanticUserError: min_items is not a valid field constraint` | Pydantic v1 syntax in v2 project | Replace `min_items=` / `max_items=` with `min_length=` / `max_length=` in `backend/schemas/analysis.py` |
| `ValidationError: value is not a valid list` | LLM returned wrong type | Check `instructor` version — `pip install instructor --upgrade` |

### SQLAlchemy Errors

| Error | Cause | Fix |
|---|---|---|
| `InvalidRequestError: Attribute name 'metadata' is reserved` | Column named `metadata` conflicts with SQLAlchemy base | Rename to `doc_metadata = Column("metadata", JSON)` in `backend/database/models.py` |
| `OperationalError: no such table` | DB not initialised | Run `python -c "from backend.database.session import engine; from backend.database.models import Base; Base.metadata.create_all(engine)"` |

### Ollama / LLM Errors

| Error | Cause | Fix |
|---|---|---|
| `httpx.ReadTimeout` | Model too large for CPU | Switch to `llama3.2:1b` in `.env` — set `OLLAMA_MODEL=llama3.2:1b` |
| `Connection refused` to `localhost:11434` | Ollama not running | Start Ollama: `ollama serve` |
| `model not found` | Model not pulled | `ollama pull llama3.2:1b` |
| `UnicodeEncodeError: 'charmap'` | Windows console encoding | Add `sys.stdout.reconfigure(encoding='utf-8')` at top of script |
| Anthropic `AuthenticationError` | Invalid / missing API key | Set key: `setx ANTHROPIC_API_KEY "sk-ant-..."` then restart terminal |
| Anthropic `402 Payment Required` | No API credits | Top up at console.anthropic.com or switch to Ollama in the sidebar |

### Dashboard Errors

| Error | Cause | Fix |
|---|---|---|
| `SyntaxError: f-string expression part cannot include a backslash` | Python < 3.12 f-string limitation | Extract nested f-string to a variable before the outer f-string (fixed in `_finding()`) |
| Dashboard shows hardcoded NovaTech data | Old standalone script still running | Use `dashboards/html_generators.py` functions directly, not `generate_cfo_dashboard.py` |
| Dashboard written to wrong folder | `_gen._ROOT` not patched | Patch `_gen._ROOT = os.path.abspath(co_dir)` before calling generators |
| `TypeError: missing required positional argument` | Engine method signatures changed | `calculate_variance_analysis(actuals, budget)` takes two separate dicts; `gaap_eng.check_all(data, kpis, variance, runway)` takes 4 args |

### Streamlit Errors

| Error | Cause | Fix |
|---|---|---|
| `StreamlitAPIException: set_page_config() can only be called once` | Called twice in session | Ensure `st.set_page_config()` is the very first Streamlit call in the file |
| Dashboard button not visible | Pipeline not run yet | Click **▶ Run Deterministic Pipeline** first — dashboard section only appears after `results` are in session state |
| `KeyError: 'results'` in main area | Page loaded before pipeline | Handled by `if "results" not in st.session_state: st.stop()` guard |
| Streamlit port 8501 already in use | Another instance running | Kill it: `netstat -ano | findstr :8501` then `taskkill /PID <pid> /F` |

### Windows-Specific Issues

| Error | Cause | Fix |
|---|---|---|
| `PermissionError` on git status | Git repo at user home sees system dirs | Normal — git warns about inaccessible Windows directories. Not an error. |
| `UnicodeEncodeError` in terminal | Windows cmd default CP1252 encoding | Run `chcp 65001` to set UTF-8, or add `PYTHONIOENCODING=utf-8` env var |
| Subprocess dashboard open fails | Path has spaces | Use `subprocess.Popen(["cmd", "/c", "start", "", abs_path])` — the empty string is required |
| Very slow Ollama inference | No dedicated GPU (Intel UHD 620) | Use `llama3.2:1b` — estimated 10–15 min for full analysis on CPU-only |

### Performance Notes

- **Math engine**: < 1 second for all KPIs, variance, forecast, anomaly detection
- **GAAP + IFRS engines**: < 1 second for all 24 standard checks
- **Dashboard generation**: < 2 seconds for all 4 HTML files
- **Ollama llama3.2:1b on CPU**: ~10–15 minutes for analysis narrative
- **Anthropic claude-sonnet-4-6**: ~10–20 seconds for analysis narrative

---

## 10. Project Structure

```
ai_cfo_system/
├── streamlit_app.py              # Main Streamlit UI
├── requirements.txt              # Pinned dependencies
├── .env.example                  # Environment variable template
├── Dockerfile                    # Docker container definition
├── docker-compose.yml
│
├── backend/
│   ├── agents/
│   │   ├── supervisor.py         # LangGraph orchestrator
│   │   ├── math_engine.py        # FinancialCalculationEngine (zero LLM)
│   │   ├── gaap_agent.py         # Calls GAAPEngine, updates state
│   │   ├── ifrs_agent.py         # Calls IFRSEngine, updates state
│   │   ├── rag_agent.py          # RAG knowledge retrieval
│   │   ├── analysis_agent.py     # LLM narrative (optional)
│   │   ├── debate_agent.py       # GAAP vs IFRS debate (optional)
│   │   ├── human_loop_node.py    # HITL approval gate
│   │   ├── reporting_agent.py    # Assembles final output
│   │   └── state.py              # CFOAgentState TypedDict
│   │
│   ├── compliance/
│   │   ├── gaap_engine.py        # 12 ASC standard checks
│   │   └── ifrs_engine.py        # 12 IASB standard checks
│   │
│   ├── schemas/
│   │   ├── analysis.py           # AnalysisOutput Pydantic model
│   │   ├── financial.py          # FinancialData Pydantic model
│   │   └── reports.py            # Report output schemas
│   │
│   ├── database/
│   │   ├── models.py             # SQLAlchemy ORM models
│   │   └── session.py            # DB session management
│   │
│   ├── rag/
│   │   ├── pipeline.py           # Embedding + retrieval pipeline
│   │   └── knowledge_base.py     # Standards knowledge base
│   │
│   ├── llm/
│   │   └── adapter.py            # Anthropic / Ollama unified client
│   │
│   └── api/
│       └── routes/               # FastAPI route handlers
│
├── dashboards/
│   └── html_generators.py        # 4 dashboard generators + agent analysis
│
├── data/
│   ├── sample_companies.py       # 3 company datasets (NovaTech/Meridian/Horizon)
│   ├── novatech/                 # Generated dashboards for NovaTech
│   │   ├── ai_cfo_dashboard.html
│   │   ├── cost_dashboard.html
│   │   ├── headcount_dashboard.html
│   │   └── inventory_dashboard.html
│   ├── meridian/                 # Generated dashboards for Meridian
│   └── horizon/                  # Generated dashboards for Horizon
│
└── tests/
    ├── test_math_engine.py
    ├── test_gaap_engine.py
    ├── test_ifrs_engine.py
    ├── test_agents.py
    └── test_rag_pipeline.py
```

---

## License

MIT — built for educational and professional use.

---

*Built with [Claude Code](https://claude.ai/code) · Anthropic claude-sonnet-4-6 · 100% local financial computation · Zero hallucination guarantee on all numerical outputs*
