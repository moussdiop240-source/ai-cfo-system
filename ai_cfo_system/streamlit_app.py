"""
AI CFO Multi-Agent System — Streamlit UI
Supports Anthropic (API key) and Ollama (local, no key needed).
Run: streamlit run streamlit_app.py
"""
import os
import sys

sys.path.insert(0, ".")

import pandas as pd
import streamlit as st

# ── page config (must be first st call) ─────────────────────────────────────
st.set_page_config(
    page_title="AI CFO System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stSidebar"] { background: #0B1120; }
  .metric-card { background: #0B1120; border: 1px solid rgba(255,255,255,0.08);
                 border-radius: 10px; padding: 16px; margin-bottom: 8px; }
  .compliant  { color: #10B981; font-weight: 700; }
  .disclosure { color: #FBBF24; font-weight: 700; }
  .noncompliant{ color: #F87171; font-weight: 700; }
  .round-header { background: linear-gradient(135deg,#0B1120,#141e33);
                  border-left: 4px solid; padding: 12px 16px;
                  border-radius: 0 8px 8px 0; margin-bottom: 12px; }
  .stButton button { width: 100%; }
</style>
""", unsafe_allow_html=True)

# ── default synthetic financial data ─────────────────────────────────────────
DEFAULT_DATA = {
    "revenue": 12_840_000, "cogs": 3_594_000, "gross_profit": 9_246_000,
    "operating_expenses": 6_120_000, "rd_expense": 2_430_000, "sg_a_expense": 3_690_000,
    "ebitda": 3_126_000, "depreciation": 312_000, "ebit": 2_814_000,
    "interest_expense": 210_000, "pre_tax_income": 2_604_000,
    "tax_provision": 573_000, "net_income": 2_031_000,
    "total_assets": 58_400_000, "current_assets": 24_100_000, "cash": 11_250_000,
    "accounts_receivable": 8_640_000, "inventory": 210_000, "prepaid_expenses": 4_000_000,
    "total_equity": 34_200_000, "current_liabilities": 9_800_000,
    "accounts_payable": 3_150_000, "deferred_revenue": 4_200_000,
    "total_debt": 14_000_000, "long_term_debt": 11_800_000,
    "cash_from_operations": 3_840_000, "capex": 780_000, "free_cash_flow": 3_060_000,
    "monthly_cash_burn": 0,
    "shares_outstanding": 8_200_000, "diluted_shares": 8_650_000,
    "rou_assets": 4_800_000, "lease_liability": 4_620_000,
    "operating_lease_expense": 360_000,
    "goodwill": 9_600_000, "goodwill_impairment_test_date": "2026-01-31",
    "impairment_test_performed": True, "impairment_tested_at_cgu_level": True,
    "allowance_for_credit_losses": 432_000,
    "ecl_stage1_allowance": 258_000, "ecl_stage2_allowance": 129_000, "ecl_stage3_allowance": 45_000,
    "revenue_recognition_policy": "ASC 606 5-step model",
    "inventory_cost_method": "fifo",
    "interest_cash_flow_classification": "operating",
    "cash_flow_policy_consistent": True, "comparative_period_presented": True,
    "publicly_listed": True, "qualifying_development_projects": True,
    "rd_dev_capitalizable_pct": 0.35,
    "actuals": {"revenue": 12_840_000, "cogs": 3_594_000, "gross_profit": 9_246_000,
                "ebitda": 3_126_000, "rd_expense": 2_430_000, "sg_a": 3_690_000},
    "budget":  {"revenue": 11_500_000, "cogs": 3_335_000, "gross_profit": 8_165_000,
                "ebitda": 2_700_000, "rd_expense": 2_100_000, "sg_a": 3_365_000},
    "historical_revenue": [7_200_000, 7_810_000, 8_450_000, 9_120_000,
                           9_980_000, 10_620_000, 11_310_000, 11_870_000, 12_840_000],
    "segments": [
        {"name": "Enterprise",           "revenue": 7_704_000, "gross_profit": 5_852_400, "assets": 32_000_000},
        {"name": "SMB",                  "revenue": 3_852_000, "gross_profit": 2_813_160, "assets": 16_000_000},
        {"name": "Professional Services","revenue": 1_284_000, "gross_profit":   580_440, "assets":  6_000_000},
    ],
    "arr": 51_360_000, "nrr_pct": 118, "churn_rate_pct": 4.2,
    "headcount": 214,
}

# ── helpers ───────────────────────────────────────────────────────────────────
def fmt(v, prefix="$", suffix=""):
    if abs(v) >= 1_000_000: return f"{prefix}{v/1_000_000:.1f}M{suffix}"
    if abs(v) >= 1_000:     return f"{prefix}{v/1_000:.0f}K{suffix}"
    return f"{prefix}{v:,.0f}{suffix}"

def status_badge(s):
    m = {"COMPLIANT": "compliant", "DISCLOSURE_REQUIRED": "disclosure", "NON_COMPLIANT": "noncompliant"}
    icons = {"COMPLIANT": "✓", "DISCLOSURE_REQUIRED": "⚠", "NON_COMPLIANT": "✗"}
    cls = m.get(s, "disclosure")
    return f'<span class="{cls}">{icons.get(s,"?")} {s}</span>'

def run_deterministic(data, company, period):
    from backend.agents.math_engine import FinancialCalculationEngine
    from backend.compliance.gaap_engine import GAAPEngine
    from backend.compliance.ifrs_engine import IFRSEngine
    from backend.rag.pipeline import RAGPipeline

    eng  = FinancialCalculationEngine()
    kpis = eng.calculate_kpis(data)
    var  = eng.calculate_variance_analysis(data["actuals"], data["budget"])
    anom = eng.detect_anomalies(data, kpis)
    run  = eng.calculate_cash_runway(data, kpis)
    fcast= eng.forecast_revenue(data["historical_revenue"], periods=8)
    recon= eng.calculate_reconciliation(data, data)

    gaap_e = GAAPEngine()
    ifrs_e = IFRSEngine()
    gaap   = gaap_e.check_all(data, kpis, var, run)
    ifrs   = ifrs_e.check_all(data, kpis, var, run)

    rag_pipeline = RAGPipeline()
    rag_q = rag_pipeline.build_rag_query({
        "task_description": f"{period} board analysis {company}",
        "task_type": "full_report", "period": period,
        "kpi_metrics": kpis, "anomaly_flags": anom,
        "gaap_results": gaap, "ifrs_results": ifrs,
    })
    chunks = rag_pipeline.retrieve(rag_q, top_k=5)

    return dict(
        kpis=kpis, variance=var, anomalies=anom, runway=run,
        forecast=fcast, reconcile=recon,
        gaap=gaap, ifrs=ifrs,
        rag_chunks=[c.to_dict() for c in chunks], rag_query=rag_q,
        company=company, period=period, data=data,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 📊 AI CFO System")
    st.caption("Multi-Agent · Anti-Hallucination · GAAP + IFRS")
    st.divider()

    # ── LLM backend ──────────────────────────────────────────────────────────
    st.markdown("### LLM Backend")
    backend_choice = st.radio(
        "Select backend",
        ["Auto-detect", "Anthropic (API key)", "Ollama (local, no key)"],
        index=0,
        label_visibility="collapsed",
    )
    backend_map = {
        "Auto-detect": "auto",
        "Anthropic (API key)": "anthropic",
        "Ollama (local, no key)": "ollama",
    }
    selected_backend = backend_map[backend_choice]

    # Anthropic key input
    if selected_backend in ("anthropic", "auto"):
        api_key_input = st.text_input(
            "Anthropic API Key",
            value=os.getenv("ANTHROPIC_API_KEY", ""),
            type="password",
            placeholder="sk-ant-...",
            help="Leave blank to use Ollama fallback",
        )
        if api_key_input:
            os.environ["ANTHROPIC_API_KEY"] = api_key_input
            from backend.llm.adapter import reset_adapter
            reset_adapter()

    # Ollama config
    if selected_backend in ("ollama", "auto"):
        ollama_host = st.text_input(
            "Ollama Host",
            value=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        )
        os.environ["OLLAMA_HOST"] = ollama_host

        # Health check + model list
        try:
            from backend.llm.adapter import LLMAdapter
            _probe = LLMAdapter(backend="ollama", ollama_host=ollama_host)
            if _probe.check_ollama_health():
                models = _probe.list_ollama_models()
                if models:
                    ollama_model = st.selectbox("Ollama Model", models)
                    os.environ["OLLAMA_MODEL"] = ollama_model
                    st.success(f"✓ Ollama running · {len(models)} model(s)")
                else:
                    st.warning("Ollama running but no models pulled.\n`ollama pull llama3.2`")
            else:
                st.error("✗ Ollama offline. Run: `ollama serve`")
        except Exception:
            ollama_model = st.text_input("Ollama Model", value="llama3.2")
            os.environ["OLLAMA_MODEL"] = ollama_model

    os.environ["LLM_BACKEND"] = selected_backend
    from backend.llm.adapter import get_adapter, reset_adapter
    reset_adapter()

    # show active status
    try:
        _a = get_adapter()
        st.caption(f"Active: {_a.status_line()}")
    except Exception as e:
        st.caption(f"Config: {e}")

    st.divider()

    # ── Company / period ──────────────────────────────────────────────────────
    st.markdown("### Report Config")
    from data.sample_companies import COMPANIES
    co_options = {f"{v['_meta']['name']} ({v['_meta']['sector']})": k for k, v in COMPANIES.items()}
    co_options["Custom (manual entry)"] = "_custom"
    selected_co_label = st.selectbox("Company Dataset", list(co_options.keys()), index=0)
    selected_co_key   = co_options[selected_co_label]

    if selected_co_key == "_custom":
        company = st.text_input("Company Name", value="My Company Inc.")
        period  = st.text_input("Period", value="Q1 2026")
        active_data = DEFAULT_DATA
    else:
        co_data = COMPANIES[selected_co_key]
        company = co_data["_meta"]["name"]
        period  = co_data["_meta"]["period"]
        active_data = co_data
        st.caption(f"Sector: {co_data['_meta']['sector']} · {co_data['_meta']['note']}")

    st.divider()

    # ── Run deterministic pipeline ────────────────────────────────────────────
    if st.button("▶  Run Deterministic Pipeline", type="primary"):
        with st.spinner("Running Math → GAAP → IFRS → RAG …"):
            try:
                st.session_state["results"] = run_deterministic(active_data, company, period)
                st.session_state["analysis"] = None
                st.session_state["debate"]   = None
                st.success("Pipeline complete!")
            except Exception as e:
                st.error(f"Pipeline error: {e}")

    # ── LLM buttons ───────────────────────────────────────────────────────────
    if "results" in st.session_state:
        if st.button("🧠  Run AI Analysis"):
            with st.spinner("Generating CFO analysis …"):
                try:
                    from backend.agents.analysis_agent import analysis_agent_node
                    r = st.session_state["results"]
                    state = {
                        "company_name": r["company"], "period": r["period"],
                        "task_description": f"{r['period']} board analysis",
                        "task_type": "full_report", "report_format": "board",
                        "validated_data": r["data"],
                        "kpi_metrics": r["kpis"], "variance_table": r["variance"],
                        "anomaly_flags": r["anomalies"], "forecast_outputs": r["forecast"],
                        "gaap_results": r["gaap"], "ifrs_results": r["ifrs"],
                        "rag_chunks": r["rag_chunks"], "errors": [], "audit_log": [],
                        "agent_statuses": {},
                    }
                    out = analysis_agent_node(state, backend=selected_backend)
                    st.session_state["analysis"] = out
                    if out.get("errors"):
                        st.warning(f"Warnings: {out['errors']}")
                    else:
                        st.success("Analysis complete!")
                except Exception as e:
                    st.error(f"Analysis error: {e}")

        if st.button("⚖  Run GAAP/IFRS Debate"):
            with st.spinner("Running 3-round debate (this takes ~60–90s) …"):
                try:
                    from backend.agents.debate_agent import debate_agent_node
                    r = st.session_state["results"]
                    state = {
                        "company_name": r["company"], "period": r["period"],
                        "validated_data": r["data"],
                        "kpi_metrics": r["kpis"],
                        "gaap_results": r["gaap"], "ifrs_results": r["ifrs"],
                        "errors": [], "audit_log": [], "agent_statuses": {},
                    }
                    out = debate_agent_node(state, backend=selected_backend)
                    st.session_state["debate"] = out
                    if out.get("errors"):
                        st.warning(f"Warnings: {out['errors']}")
                    else:
                        st.success("Debate complete!")
                except Exception as e:
                    st.error(f"Debate error: {e}")

    st.divider()
    st.markdown("### 📊 Dashboards")
    if "results" in st.session_state:
        if st.button("🖥  Generate All Dashboards", type="primary"):
            with st.spinner("Generating 4 dashboards …"):
                try:
                    import subprocess

                    from dashboards.html_generators import (
                        generate_cfo_dashboard,
                        generate_cost_dashboard,
                        generate_headcount_dashboard,
                        generate_inventory_dashboard,
                    )
                    r = st.session_state["results"]
                    paths = []
                    paths.append(generate_cfo_dashboard(
                        r["data"], r["kpis"], r["variance"], r["gaap"], r["ifrs"],
                        r["forecast"], r["runway"], r["anomalies"], r["rag_chunks"],
                        r["company"], r["period"],
                    ))
                    paths.append(generate_cost_dashboard(r["data"], r["kpis"], r["company"], r["period"]))
                    paths.append(generate_headcount_dashboard(r["data"], r["kpis"], r["company"], r["period"]))
                    paths.append(generate_inventory_dashboard(r["data"], r["kpis"], r["company"], r["period"]))
                    for p in paths:
                        subprocess.Popen(["cmd", "/c", "start", "", p], shell=False)
                    st.success("✓ All 4 dashboards generated and opened!")
                    st.session_state["dashboard_paths"] = paths
                except Exception as e:
                    st.error(f"Dashboard error: {e}")

        if "dashboard_paths" in st.session_state:
            st.caption("Last generated:")
            names = ["AI CFO", "Cost Analysis", "Headcount KPI", "Inventory"]
            for name, path in zip(names, st.session_state["dashboard_paths"]):
                if st.button(f"↗ Open {name}", key=f"open_{name}"):
                    import subprocess
                    subprocess.Popen(["cmd", "/c", "start", "", path], shell=False)
    else:
        st.caption("Run the pipeline first to enable dashboards.")

    st.divider()
    st.caption("Layer 1: Pandas/NumPy/Sklearn · ZERO LLM\nLayer 2: Pydantic v2 schemas\nLayer 3: FastAPI + pgvector\nLayer 4: RAG retrieved context")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN AREA
# ══════════════════════════════════════════════════════════════════════════════
if "results" not in st.session_state:
    st.markdown("## Welcome to the AI CFO Multi-Agent System")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**Step 1** — Configure LLM backend in the sidebar (Anthropic or Ollama)")
    with col2:
        st.info("**Step 2** — Click **Run Deterministic Pipeline** to compute all KPIs, GAAP, IFRS, and RAG")
    with col3:
        st.info("**Step 3** — Click **Run AI Analysis** or **Run GAAP/IFRS Debate** for LLM interpretation")
    st.stop()

r = st.session_state["results"]
kpis = r["kpis"]
data = r["data"]

# ── header ───────────────────────────────────────────────────────────────────
gc = sum(1 for v in r["gaap"].values() if v.get("status") == "COMPLIANT")
ic = sum(1 for v in r["ifrs"].values() if v.get("status") == "COMPLIANT")

st.markdown(f"## {r['company']} — {r['period']}")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Revenue",      fmt(data["revenue"]))
c2.metric("EBITDA Margin", f"{kpis['ebitda_margin_pct']:.1f}%")
c3.metric("Gross Margin",  f"{kpis['gross_margin_pct']:.1f}%")
c4.metric("GAAP",         f"{gc}/12 ✓")
c5.metric("IFRS",         f"{ic}/12 ✓")
st.divider()

# ── tabs ──────────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "📈 Overview & KPIs",
    "📊 Variance Analysis",
    "⚖ Compliance",
    "🔮 Forecast & Segments",
    "↔ GAAP/IFRS Recon",
    "🧠 AI Analysis",
    "💬 Debate",
    "🔍 RAG & Audit",
])


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 1 · OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.subheader("Income Statement KPIs")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Revenue",      fmt(data["revenue"]),    f"vs budget {fmt(data['budget']['revenue'])}")
    c2.metric("Gross Profit", fmt(data["gross_profit"]),f"GM {kpis['gross_margin_pct']:.1f}%")
    c3.metric("EBITDA",       fmt(data["ebitda"]),      f"Margin {kpis['ebitda_margin_pct']:.1f}%")
    c4.metric("Net Income",   fmt(data["net_income"]),  f"NM {kpis['net_margin_pct']:.1f}%")

    st.subheader("Balance Sheet & Liquidity")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cash",           fmt(data["cash"]))
    c2.metric("Current Ratio",  f"{kpis['current_ratio']:.2f}x",
              "✓ Healthy" if kpis["current_ratio"] >= 2 else "⚠ Monitor")
    c3.metric("Net Debt",       fmt(kpis["net_debt"]))
    c4.metric("Working Capital",fmt(kpis["working_capital"]))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ROE",             f"{kpis['roe_pct']:.1f}%")
    c2.metric("ROA",             f"{kpis['roa_pct']:.1f}%")
    c3.metric("D/E Ratio",       f"{kpis['debt_to_equity']:.2f}x")
    c4.metric("Diluted EPS",     f"${kpis['diluted_eps']:.2f}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("DSO",     f"{kpis['dso_days']:.0f} days")
    c2.metric("CCC",     f"{kpis['ccc_days']:.0f} days")
    c3.metric("Int. Coverage", f"{kpis['interest_coverage']:.1f}x")
    c4.metric("Eff. Tax Rate",  f"{kpis['effective_tax_rate']:.1f}%")

    st.subheader("SaaS Metrics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ARR",    fmt(data["arr"]))
    c2.metric("NRR",    f"{data['nrr_pct']}%")
    c3.metric("Churn",  f"{data['churn_rate_pct']}%")
    c4.metric("Headcount", str(data["headcount"]))

    # Anomalies
    if r["anomalies"]:
        st.subheader("Anomaly Flags")
        for flag in r["anomalies"]:
            if "CRITICAL" in flag:
                st.error(flag)
            else:
                st.warning(flag)
    else:
        st.success("✓ No statistical anomalies detected — all indicators within normal bounds")

    # Cash runway
    runway = r["runway"]
    st.subheader("Cash Runway (ASC 205-40)")
    rm = runway["runway_months"]
    label = "∞ Profitable" if rm > 900 else f"{rm} months"
    if runway["status"] == "ADEQUATE":
        st.success(f"✓ {label} — ASC 205-40 not applicable (> 12 months)")
    elif runway["status"] == "WARNING":
        st.warning(f"⚠ {label} — Approaching 12-month going concern threshold")
    else:
        st.error(f"✗ {label} — ASC 205-40 going concern disclosure required")


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 2 · VARIANCE
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.subheader("Budget vs Actuals — SAB 99 Materiality (≥ 5%)")

    rows = []
    labels = {"revenue": "Revenue", "cogs": "Cost of Revenue",
              "gross_profit": "Gross Profit", "ebitda": "EBITDA",
              "rd_expense": "R&D Expense", "sg_a": "SG&A Expense"}
    for key, label in labels.items():
        item = r["variance"]["line_items"].get(key, {})
        if not item:
            continue
        rows.append({
            "Line Item":    label,
            "Actual":       fmt(item["actual"]),
            "Budget":       fmt(item["budget"]),
            "Variance $":   fmt(item["variance_abs"]),
            "Variance %":   f"{item['variance_pct']:+.1f}%",
            "Favorable":    "✓" if item["favorable"] else "✗",
            "Material (SAB 99)": "⚠ Yes" if item["material"] else "No",
        })

    t = r["variance"]["totals"]
    rows.append({
        "Line Item": "TOTAL",
        "Actual":    fmt(t["actual"]),
        "Budget":    fmt(t["budget"]),
        "Variance $": fmt(t["variance_abs"]),
        "Variance %": f"{t['variance_pct']:+.1f}%",
        "Favorable":  "✓" if t["favorable"] else "✗",
        "Material (SAB 99)": "—",
    })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Variance bar chart
    st.subheader("Variance Bridge")
    chart_data = {k: v["variance_abs"]
                  for k, v in r["variance"]["line_items"].items()
                  if k in labels}
    chart_df = pd.DataFrame.from_dict(
        {"Line Item": list(labels[k] for k in chart_data),
         "Variance": list(chart_data.values())}
    )
    st.bar_chart(chart_df.set_index("Line Item"))


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 3 · COMPLIANCE
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    col_g, col_i = st.columns(2)

    gaap_labels = {
        "asc205": "ASC 205-40 Going Concern", "asc230": "ASC 230 Cash Flows",
        "asc260": "ASC 260 EPS",              "asc280": "ASC 280 Segments",
        "asc310": "ASC 310/326 CECL",         "asc350": "ASC 350 Goodwill",
        "asc450": "ASC 450 Contingencies",    "asc606": "ASC 606 Revenue",
        "asc740": "ASC 740 Income Taxes",     "asc820": "ASC 820 Fair Value",
        "asc842": "ASC 842 Leases",           "sab99":  "SAB 99 Materiality",
    }
    ifrs_labels = {
        "ias1":  "IAS 1 Presentation",  "ias2":  "IAS 2 Inventories",
        "ias7":  "IAS 7 Cash Flows",    "ias12": "IAS 12 Income Taxes",
        "ias16": "IAS 16 PPE",          "ias33": "IAS 33 EPS",
        "ias36": "IAS 36 Impairment",   "ias37": "IAS 37 Provisions",
        "ias38": "IAS 38 Intangibles",  "ifrs9": "IFRS 9 Credit Losses",
        "ifrs15":"IFRS 15 Revenue",     "ifrs16":"IFRS 16 Leases",
    }

    with col_g:
        gc = sum(1 for v in r["gaap"].values() if v.get("status") == "COMPLIANT")
        st.metric("GAAP Compliant", f"{gc}/12")
        gaap_rows = []
        for std, label in gaap_labels.items():
            res = r["gaap"].get(std, {})
            gaap_rows.append({
                "Standard": label,
                "Status":   res.get("status", "—"),
                "Finding":  res.get("finding", "—")[:90],
            })
        gdf = pd.DataFrame(gaap_rows)

        def color_status(val):
            c = {"COMPLIANT": "color: #10B981", "DISCLOSURE_REQUIRED": "color: #FBBF24",
                 "NON_COMPLIANT": "color: #F87171"}
            return c.get(val, "")

        st.dataframe(
            gdf.style.applymap(color_status, subset=["Status"]),
            use_container_width=True, hide_index=True,
        )

    with col_i:
        ic = sum(1 for v in r["ifrs"].values() if v.get("status") == "COMPLIANT")
        st.metric("IFRS Compliant", f"{ic}/12")
        ifrs_rows = []
        for std, label in ifrs_labels.items():
            res = r["ifrs"].get(std, {})
            ifrs_rows.append({
                "Standard": label,
                "Status":   res.get("status", "—"),
                "Finding":  res.get("finding", "—")[:90],
            })
        idf = pd.DataFrame(ifrs_rows)
        st.dataframe(
            idf.style.applymap(color_status, subset=["Status"]),
            use_container_width=True, hide_index=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 4 · FORECAST & SEGMENTS
# ══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.subheader("Revenue Forecast — LR 40% + Holt-Winters 60% Ensemble")

    hist   = data["historical_revenue"]
    fcast  = r["forecast"].get("forecast", [])
    q_hist = ["Q1'24","Q2'24","Q3'24","Q4'24","Q1'25","Q2'25","Q3'25","Q4'25","Q1'26"]
    q_fcast= ["Q2'26","Q3'26","Q4'26","Q1'27","Q2'27","Q3'27","Q4'27","Q1'28"]

    chart_rows = (
        [{"Quarter": q, "Revenue": v, "Type": "Historical"} for q, v in zip(q_hist, hist)] +
        [{"Quarter": q, "Revenue": v, "Type": "Forecast"}   for q, v in zip(q_fcast, fcast)]
    )
    fdf = pd.DataFrame(chart_rows)
    st.line_chart(fdf.pivot(index="Quarter", columns="Type", values="Revenue"))

    if r["forecast"].get("r2") is not None:
        st.caption(
            f"R² = {r['forecast']['r2']:.4f} · "
            f"Method: {r['forecast'].get('method','')} · "
            f"Next Q: {fmt(fcast[0]) if fcast else 'N/A'}"
        )

    st.divider()
    st.subheader("Segment Analysis (ASC 280 — 10% threshold)")

    segs = data["segments"]
    seg_rows = []
    total_rev = sum(s["revenue"] for s in segs)
    for s in segs:
        gm = round(s["gross_profit"] / s["revenue"] * 100, 1) if s["revenue"] else 0
        seg_rows.append({
            "Segment":      s["name"],
            "Revenue":      fmt(s["revenue"]),
            "% of Total":   f"{s['revenue']/total_rev*100:.1f}%",
            "Gross Profit": fmt(s["gross_profit"]),
            "Gross Margin": f"{gm:.1f}%",
            "Assets":       fmt(s["assets"]),
            "Reportable?":  "✓ Yes" if s["revenue"]/total_rev >= 0.10 else "No",
        })
    st.dataframe(pd.DataFrame(seg_rows), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 5 · GAAP↔IFRS RECONCILIATION
# ══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.subheader("GAAP-to-IFRS Key Reconciling Items")

    op_lease = data["operating_lease_expense"]
    rd       = data["rd_expense"]
    dev_pct  = data.get("rd_dev_capitalizable_pct", 0.35)

    recon_rows = [
        {
            "Topic":           "IFRS 16 vs ASC 842 — Leases",
            "GAAP Treatment":  "Dual model — operating leases in SG&A (ASC 842)",
            "IFRS Treatment":  "Single model — all leases capitalized (IFRS 16)",
            "P&L / BS Impact": fmt(op_lease),
            "Effect":          "EBITDA higher under IFRS",
        },
        {
            "Topic":           "IAS 38 vs ASC 730 — R&D",
            "GAAP Treatment":  "All R&D expensed immediately (ASC 730)",
            "IFRS Treatment":  f"~{dev_pct*100:.0f}% dev costs capitalizable (IAS 38)",
            "P&L / BS Impact": fmt(rd * dev_pct),
            "Effect":          "Net income higher under IFRS",
        },
        {
            "Topic":           "IAS 37 vs ASC 450 — Provisions",
            "GAAP Treatment":  "~75% probable threshold (ASC 450)",
            "IFRS Treatment":  ">50% probable threshold (IAS 37)",
            "P&L / BS Impact": "Qualitative",
            "Effect":          "Earlier recognition under IFRS",
        },
        {
            "Topic":           "IAS 36 vs ASC 350 — Goodwill",
            "GAAP Treatment":  "No impairment reversal (ASC 350)",
            "IFRS Treatment":  "Reversal permitted at CGU level (IAS 36)",
            "P&L / BS Impact": fmt(data["goodwill"]),
            "Effect":          "IFRS allows upside recovery",
        },
        {
            "Topic":           "IAS 2 vs ASC 330 — Inventory",
            "GAAP Treatment":  "LIFO / FIFO / Weighted avg (ASC 330)",
            "IFRS Treatment":  "LIFO STRICTLY PROHIBITED (IAS 2)",
            "P&L / BS Impact": "N/A — company uses FIFO",
            "Effect":          "Compliant under both",
        },
        {
            "Topic":           "IAS 7 vs ASC 230 — Cash Flows",
            "GAAP Treatment":  "Interest paid = Operating (mandatory, ASC 230)",
            "IFRS Treatment":  "Interest paid = Operating OR Financing (policy choice, IAS 7)",
            "P&L / BS Impact": fmt(data["interest_expense"]),
            "Effect":          "IFRS gives flexibility",
        },
    ]

    col1, col2 = st.columns(2)
    with col1:
        st.metric("IFRS EBITDA Uplift",
                  fmt(data["ebitda"] + op_lease),
                  f"+{fmt(op_lease)} vs GAAP EBITDA {fmt(data['ebitda'])}")
    with col2:
        st.metric("IAS 38 R&D Capitalisation Benefit",
                  fmt(rd * dev_pct),
                  f"{dev_pct*100:.0f}% of {fmt(rd)} R&D")

    st.dataframe(pd.DataFrame(recon_rows), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 6 · AI ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
with tabs[5]:
    analysis = st.session_state.get("analysis")

    if not analysis:
        st.info("Click **🧠 Run AI Analysis** in the sidebar to generate CFO interpretation.")
        st.caption("Works with Anthropic (API key) or Ollama (local model, no key needed).")
    else:
        s = analysis.get("structured_output") or analysis

        # Executive Summary
        st.subheader("Executive Summary")
        summary = s.get("analysis_narrative") or s.get("executive_summary", "")
        st.markdown(summary)

        col1, col2 = st.columns(2)
        with col1:
            conf = s.get("ai_confidence_score") or s.get("confidence_score", 0)
            st.metric("Confidence Score", f"{conf:.0%}")

        # Key Variance Drivers
        drivers = s.get("key_variance_drivers", [])
        if drivers:
            st.subheader("Key Variance Drivers")
            for d in drivers:
                st.markdown(f"- {d}")

        col1, col2 = st.columns(2)
        with col1:
            risks = s.get("identified_risks", [])
            if risks:
                st.subheader("Identified Risks")
                for risk in risks:
                    st.warning(risk)

        with col2:
            opps = s.get("opportunities", [])
            if opps:
                st.subheader("Opportunities")
                for opp in opps:
                    st.success(opp)

        # Action Items
        actions = s.get("action_items", [])
        if actions:
            st.subheader("Action Items (with Owners)")
            for i, a in enumerate(actions, 1):
                st.markdown(f"**{i}.** {a}")

        # Citations
        with st.expander("Citations & Sources"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**RAG Sources**")
                for c in s.get("rag_sources_cited", []):
                    st.caption(c)
            with col2:
                st.markdown("**GAAP Citations**")
                for c in s.get("gaap_citations", []):
                    st.caption(c)
            with col3:
                st.markdown("**IFRS Citations**")
                for c in s.get("ifrs_citations", []):
                    st.caption(c)

        # Errors if any
        if analysis.get("errors"):
            with st.expander("Warnings"):
                for e in analysis["errors"]:
                    st.caption(e)


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 7 · DEBATE
# ══════════════════════════════════════════════════════════════════════════════
with tabs[6]:
    debate = st.session_state.get("debate")

    if not debate:
        st.info("Click **⚖ Run GAAP/IFRS Debate** in the sidebar to start the 3-round debate.")
        st.caption("Round 1: IFRS Advocate → Round 2: GAAP Advocate → Round 3: Independent Arbiter")
    else:
        # Round 1
        st.markdown(
            '<div class="round-header" style="border-color:#A78BFA">'
            '<strong style="color:#A78BFA">ROUND 1 — IFRS ADVOCATE</strong><br>'
            '<small>IASB expert · 25yr international experience</small></div>',
            unsafe_allow_html=True,
        )
        ifrs_arg = debate.get("debate_ifrs_advocate", "")
        st.markdown(ifrs_arg)

        st.divider()

        # Round 2
        st.markdown(
            '<div class="round-header" style="border-color:#60A5FA">'
            '<strong style="color:#60A5FA">ROUND 2 — GAAP ADVOCATE</strong><br>'
            '<small>FASB/SEC expert · 25yr NYSE/NASDAQ experience</small></div>',
            unsafe_allow_html=True,
        )
        gaap_arg = debate.get("debate_gaap_advocate", "")
        st.markdown(gaap_arg)

        st.divider()

        # Round 3
        st.markdown(
            '<div class="round-header" style="border-color:#10B981">'
            '<strong style="color:#10B981">ROUND 3 — INDEPENDENT ARBITER · VERDICT</strong><br>'
            '<small>IASB + FASB advisory council · No bias · Binding recommendation</small></div>',
            unsafe_allow_html=True,
        )
        arbiter = debate.get("debate_arbiter", "")
        st.markdown(arbiter)

        if debate.get("errors"):
            with st.expander("Warnings"):
                for e in debate["errors"]:
                    st.caption(e)


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 8 · RAG & AUDIT
# ══════════════════════════════════════════════════════════════════════════════
with tabs[7]:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("RAG — Retrieved Knowledge Chunks")
        st.caption(f"Query: {r['rag_query'][:120]}…")
        for i, chunk in enumerate(r["rag_chunks"], 1):
            with st.expander(f"[{i}] {chunk['title']} — score: {chunk.get('score', 0):.3f}"):
                st.markdown(chunk["content"])

    with col2:
        st.subheader("Pipeline Status")
        pipeline_status = {
            "data_agent":     ("COMPLETE", "✓"),
            "math_engine":    ("COMPLETE", "✓"),
            "rag_agent":      ("COMPLETE", "✓"),
            "gaap_agent":     ("COMPLETE", "✓"),
            "ifrs_agent":     ("COMPLETE", "✓"),
            "analysis_agent": ("COMPLETE" if st.session_state.get("analysis") and
                               not st.session_state["analysis"].get("errors") else "PENDING", ""),
            "debate_agent":   ("COMPLETE" if st.session_state.get("debate") and
                               not st.session_state["debate"].get("errors") else "PENDING", ""),
            "reporting_agent":("PENDING", ""),
        }
        for agent, (status, _) in pipeline_status.items():
            if status == "COMPLETE":
                st.success(f"✓ {agent}")
            else:
                st.info(f"○ {agent}")

        st.divider()
        st.subheader("LLM Backend")
        try:
            _a = get_adapter()
            st.code(_a.status_line())
        except Exception as e:
            st.caption(str(e))

        st.divider()
        st.subheader("Data Quality")
        req = ["revenue","cogs","gross_profit","ebitda","net_income","total_assets","total_equity","cash"]
        score = sum(1 for f in req if data.get(f)) / len(req)
        st.metric("Completeness", f"{score:.0%}")
        st.progress(score)
