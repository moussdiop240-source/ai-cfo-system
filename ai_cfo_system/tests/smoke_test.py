"""
CI smoke tests — runs deterministic pipeline end-to-end for all 3 companies
and verifies all 12 HTML dashboards are generated and non-empty.
No LLM calls are made.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import dashboards.html_generators as _gen
from backend.agents.math_engine import FinancialCalculationEngine
from backend.compliance.gaap_engine import GAAPEngine
from backend.compliance.ifrs_engine import IFRSEngine
from data.sample_companies import COMPANIES

ACTUALS_KEYS = [
    "revenue", "cogs", "gross_profit", "ebitda", "ebit", "net_income",
    "rd_expense", "sg_a_expense", "operating_expenses", "interest_expense",
    "tax_provision", "capex", "free_cash_flow", "depreciation_amortization",
]

RAG_CHUNKS = [
    {"title": "ASC 606", "content": "Revenue recognised when obligations satisfied."},
    {"title": "SAB 99",  "content": "5% materiality threshold."},
]


def test_math_engine_kpis():
    eng = FinancialCalculationEngine()
    data = {
        "revenue": 10_000_000, "cogs": 3_000_000, "gross_profit": 7_000_000,
        "ebitda": 2_000_000, "ebit": 1_800_000, "net_income": 1_200_000,
        "total_assets": 20_000_000, "total_equity": 12_000_000,
        "current_assets": 8_000_000, "current_liabilities": 3_000_000,
        "cash": 4_000_000, "accounts_receivable": 2_000_000,
        "accounts_payable": 1_000_000, "inventory": 500_000,
        "total_debt": 5_000_000, "interest_expense": 200_000,
        "shares_outstanding": 1_000_000, "diluted_shares": 1_050_000,
        "tax_provision": 300_000, "pre_tax_income": 1_500_000,
    }
    kpis = eng.calculate_kpis(data)
    assert kpis["gross_margin_pct"] == 70.0, f"Expected 70.0, got {kpis['gross_margin_pct']}"
    assert kpis["net_margin_pct"] == 12.0,   f"Expected 12.0, got {kpis['net_margin_pct']}"
    assert kpis["current_ratio"] > 0
    print("  OK: math engine KPIs")


def test_gaap_ifrs_all_companies():
    math_eng = FinancialCalculationEngine()
    gaap_eng = GAAPEngine()
    ifrs_eng = IFRSEngine()

    for key, data in COMPANIES.items():
        actuals  = {k: float(data[k]) for k in ACTUALS_KEYS if k in data}
        kpis     = math_eng.calculate_kpis(data)
        variance = math_eng.calculate_variance_analysis(actuals, data.get("budget", {}))
        runway   = math_eng.calculate_cash_runway(data, kpis)
        gaap     = gaap_eng.check_all(data, kpis, variance, runway)
        ifrs     = ifrs_eng.check_all(data, kpis, variance, runway)

        assert len(gaap) == 12, f"{key}: expected 12 GAAP checks, got {len(gaap)}"
        assert len(ifrs) == 12, f"{key}: expected 12 IFRS checks, got {len(ifrs)}"
        gc = sum(1 for v in gaap.values() if v.get("status") == "COMPLIANT")
        ic = sum(1 for v in ifrs.values() if v.get("status") == "COMPLIANT")
        print(f"  OK: {data['_meta']['name']} — GAAP {gc}/12  IFRS {ic}/12")


def test_dashboard_generation():
    math_eng = FinancialCalculationEngine()
    gaap_eng = GAAPEngine()
    ifrs_eng = IFRSEngine()
    generated = []

    with tempfile.TemporaryDirectory() as tmp:
        for key, data in COMPANIES.items():
            co_dir = os.path.join(tmp, key)
            os.makedirs(co_dir)
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
            _gen._ROOT = co_dir
            paths = [
                _gen.generate_cfo_dashboard(data, kpis, variance, gaap, ifrs,
                                            forecast, runway, anomalies,
                                            RAG_CHUNKS, name, period),
                _gen.generate_cost_dashboard(data, kpis, name, period),
                _gen.generate_headcount_dashboard(data, kpis, name, period),
                _gen.generate_inventory_dashboard(data, kpis, name, period),
            ]
            _gen._ROOT = orig

            for p in paths:
                assert os.path.exists(p), f"Missing: {p}"
                size = os.path.getsize(p)
                assert size > 10_000, f"Too small ({size} bytes): {p}"
            generated.extend(paths)
            print(f"  OK: {name} — 4 dashboards ({min(os.path.getsize(p) for p in paths)//1024}KB min)")

    print(f"  OK: {len(generated)} dashboards total")


if __name__ == "__main__":
    print("Running smoke tests...")
    test_math_engine_kpis()
    test_gaap_ifrs_all_companies()
    test_dashboard_generation()
    print("\nAll smoke tests passed.")
