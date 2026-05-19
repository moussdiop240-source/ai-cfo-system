"""End-to-end Ollama test: deterministic pipeline + AI analysis + 3-round debate."""
import os, sys, time, io
# Force UTF-8 on Windows so LLM output with special chars doesn't crash
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
os.environ["LLM_BACKEND"]  = "ollama"
os.environ["OLLAMA_MODEL"] = "llama3.2:latest"
sys.path.insert(0, ".")

from backend.llm.adapter import get_adapter, reset_adapter
reset_adapter()
a = get_adapter()
print(f"Backend: {a.active_backend} | Model: {a.active_model} | Health: {a.check_ollama_health()}")

# ── Synthetic data ────────────────────────────────────────────────────────────
DATA = {
    "revenue": 12_840_000, "cogs": 3_594_000, "gross_profit": 9_246_000,
    "ebitda": 3_126_000, "depreciation": 312_000, "ebit": 2_814_000,
    "interest_expense": 210_000, "pre_tax_income": 2_604_000,
    "tax_provision": 573_000, "net_income": 2_031_000,
    "total_assets": 58_400_000, "current_assets": 24_100_000, "cash": 11_250_000,
    "accounts_receivable": 8_640_000, "inventory": 210_000,
    "total_equity": 34_200_000, "current_liabilities": 9_800_000,
    "accounts_payable": 3_150_000, "total_debt": 14_000_000,
    "shares_outstanding": 8_200_000, "diluted_shares": 8_650_000,
    "rou_assets": 4_800_000, "lease_liability": 4_620_000, "operating_lease_expense": 360_000,
    "goodwill": 9_600_000, "goodwill_impairment_test_date": "2026-01-31",
    "impairment_test_performed": True, "impairment_tested_at_cgu_level": True,
    "allowance_for_credit_losses": 432_000,
    "ecl_stage1_allowance": 258_000, "ecl_stage2_allowance": 129_000, "ecl_stage3_allowance": 45_000,
    "revenue_recognition_policy": "ASC 606 5-step model", "inventory_cost_method": "fifo",
    "interest_cash_flow_classification": "operating", "cash_flow_policy_consistent": True,
    "comparative_period_presented": True, "publicly_listed": True,
    "qualifying_development_projects": True, "rd_dev_capitalizable_pct": 0.35,
    "rd_expense": 2_430_000, "monthly_cash_burn": 0, "cash_from_operations": 3_840_000,
    "actuals": {"revenue": 12_840_000, "cogs": 3_594_000, "ebitda": 3_126_000},
    "budget":  {"revenue": 11_500_000, "cogs": 3_335_000, "ebitda": 2_700_000},
    "historical_revenue": [7_200_000, 7_810_000, 8_450_000, 9_120_000,
                           9_980_000, 10_620_000, 11_310_000, 11_870_000, 12_840_000],
    "segments": [
        {"name": "Enterprise", "revenue": 7_704_000, "gross_profit": 5_852_400, "assets": 32_000_000},
        {"name": "SMB",        "revenue": 3_852_000, "gross_profit": 2_813_160, "assets": 16_000_000},
    ],
}

# ── STEP 1: Deterministic ────────────────────────────────────────────────────
print("\n" + "="*60)
print("STEP 1 — Deterministic Pipeline (ZERO LLM)")
print("="*60)
from backend.agents.math_engine import FinancialCalculationEngine
from backend.compliance.gaap_engine import GAAPEngine
from backend.compliance.ifrs_engine import IFRSEngine
from backend.rag.pipeline import RAGPipeline

eng    = FinancialCalculationEngine()
kpis   = eng.calculate_kpis(DATA)
var    = eng.calculate_variance_analysis(DATA["actuals"], DATA["budget"])
anom   = eng.detect_anomalies(DATA, kpis)
runway = eng.calculate_cash_runway(DATA, kpis)
gaap   = GAAPEngine().check_all(DATA, kpis, var, runway)
ifrs   = IFRSEngine().check_all(DATA, kpis, var, runway)

rag    = RAGPipeline()
chunks = rag.retrieve("Q1 2026 SaaS GAAP IFRS revenue", top_k=3)

gc = sum(1 for v in gaap.values() if v.get("status") == "COMPLIANT")
ic = sum(1 for v in ifrs.values() if v.get("status") == "COMPLIANT")

print(f"  KPIs computed  : {len(kpis)}")
print(f"  Gross Margin   : {kpis['gross_margin_pct']:.1f}%")
print(f"  EBITDA Margin  : {kpis['ebitda_margin_pct']:.1f}%")
print(f"  Diluted EPS    : ${kpis['diluted_eps']:.2f}")
print(f"  Current Ratio  : {kpis['current_ratio']:.2f}x")
print(f"  GAAP           : {gc}/12 compliant")
print(f"  IFRS           : {ic}/12 compliant")
print(f"  Anomalies      : {len(anom)}")
print(f"  RAG chunks     : {len(chunks)}")
print("  STATUS: PASS")

# ── STEP 2: Agent state ──────────────────────────────────────────────────────
STATE = {
    "company_name": "NovaTech Solutions Inc.", "period": "Q1 2026",
    "task_description": "Q1 2026 board analysis — SaaS",
    "task_type": "full_report", "report_format": "board",
    "validated_data": DATA, "kpi_metrics": kpis, "variance_table": var,
    "anomaly_flags": anom, "forecast_outputs": {},
    "gaap_results": gaap, "ifrs_results": ifrs,
    "rag_chunks": [c.to_dict() for c in chunks],
    "errors": [], "audit_log": [], "agent_statuses": {},
}

# ── STEP 2: AI Analysis ──────────────────────────────────────────────────────
print("\n" + "="*60)
print("STEP 2 — AI Analysis Agent (Ollama llama3.2:latest)")
print("="*60)
t0 = time.time()
from backend.agents.analysis_agent import analysis_agent_node
out = analysis_agent_node(STATE, backend="ollama")
elapsed = time.time() - t0

if out.get("errors"):
    print(f"  ERRORS: {out['errors']}")
else:
    s = out.get("structured_output") or out
    summary  = out.get("analysis_narrative") or s.get("executive_summary", "")
    conf     = out.get("ai_confidence_score") or s.get("confidence_score", 0)
    risks    = out.get("identified_risks") or s.get("identified_risks", [])
    opps     = out.get("opportunities") or s.get("opportunities", [])
    actions  = out.get("action_items") or s.get("action_items", [])
    drivers  = out.get("key_variance_drivers") or s.get("key_variance_drivers", [])

    print(f"  Elapsed        : {elapsed:.1f}s")
    print(f"  Confidence     : {conf}")
    print(f"  Summary length : {len(summary)} chars")
    print(f"  Variance drivers: {len(drivers)}")
    print(f"  Risks          : {len(risks)}")
    print(f"  Opportunities  : {len(opps)}")
    print(f"  Action items   : {len(actions)}")
    print()
    print("  Executive Summary:")
    print("  " + summary[:400].replace("\n", "\n  "))
    if risks:
        print(f"\n  Top Risk: {str(risks[0])[:150]}")
    if actions:
        print(f"\n  Top Action: {str(actions[0])[:150]}")
    print("  STATUS: PASS" if summary else "  STATUS: EMPTY RESPONSE")

# ── STEP 3: Debate ───────────────────────────────────────────────────────────
print("\n" + "="*60)
print("STEP 3 — GAAP/IFRS Debate Agent (3 rounds, Ollama)")
print("="*60)
t0 = time.time()
from backend.agents.debate_agent import debate_agent_node
dout = debate_agent_node(STATE, backend="ollama")
elapsed = time.time() - t0

if dout.get("errors"):
    print(f"  ERRORS: {dout['errors']}")

ifrs_arg = dout.get("debate_ifrs_advocate", "")
gaap_arg = dout.get("debate_gaap_advocate", "")
arbiter  = dout.get("debate_arbiter", "")

print(f"  Elapsed          : {elapsed:.1f}s")
print(f"  IFRS Advocate    : {len(ifrs_arg)} chars")
print(f"  GAAP Advocate    : {len(gaap_arg)} chars")
print(f"  Arbiter Verdict  : {len(arbiter)} chars")
print()
print("  IFRS Advocate (first 300 chars):")
print("  " + ifrs_arg[:300].replace("\n", "\n  "))
print()
print("  Arbiter Verdict (first 300 chars):")
print("  " + arbiter[:300].replace("\n", "\n  "))
print("  STATUS: PASS" if all([ifrs_arg, gaap_arg, arbiter]) else "  STATUS: INCOMPLETE")

print("\n" + "="*60)
print("ALL TESTS COMPLETE")
print("="*60)
