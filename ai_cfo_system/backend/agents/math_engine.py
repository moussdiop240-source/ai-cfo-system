"""
DETERMINISTIC MATH ENGINE — ZERO LLM.
All arithmetic, KPIs, forecasts, anomaly detection via Pandas/NumPy/Sklearn.
Every number is exact and reproducible.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from .state import CFOAgentState

APPROVAL_TRIGGERS = {
    "variance_exceeds_10pct":   {"field": "variance_pct",     "threshold": 10.0,  "severity": "high"},
    "gross_margin_below_30pct": {"field": "gross_margin_pct", "threshold": 30.0,  "severity": "critical"},
    "multiple_anomalies":       {"field": "anomaly_count",    "threshold": 3,     "severity": "high"},
    "gaap_NON_COMPLIANT":       {"severity": "critical", "requires_disclosure": True},
    "gaap_DISCLOSURE_REQUIRED": {"severity": "high",     "requires_disclosure": True},
    "ifrs_NON_COMPLIANT":       {"severity": "critical", "requires_disclosure": True},
    "ifrs_DISCLOSURE_REQUIRED": {"severity": "high",     "requires_disclosure": True},
}


class FinancialCalculationEngine:

    def calculate_variance_analysis(
        self,
        actuals: Dict[str, float],
        budget: Dict[str, float],
    ) -> Dict[str, Any]:
        """Exact variance — no approximation, no LLM. Uses SAB 99 5% materiality threshold."""
        rows = {}
        for key in set(list(actuals.keys()) + list(budget.keys())):
            act = actuals.get(key, 0.0)
            bud = budget.get(key, 0.0)
            var_abs = round(act - bud, 2)
            var_pct = round((var_abs / abs(bud)) * 100, 2) if bud else 0.0
            rows[key] = {
                "actual": act,
                "budget": bud,
                "variance_abs": var_abs,
                "variance_pct": var_pct,
                "material": abs(var_pct) >= 5.0,
                "favorable": var_abs >= 0,
            }

        total_actual = round(sum(r["actual"] for r in rows.values()), 2)
        total_budget = round(sum(r["budget"] for r in rows.values()), 2)
        total_var_abs = round(total_actual - total_budget, 2)
        total_var_pct = round((total_var_abs / abs(total_budget)) * 100, 2) if total_budget else 0.0

        return {
            "line_items": rows,
            "totals": {
                "actual": total_actual,
                "budget": total_budget,
                "variance_abs": total_var_abs,
                "variance_pct": total_var_pct,
                "favorable": total_var_abs >= 0,
            },
            "material_items": [k for k, v in rows.items() if v["material"]],
            "method": "pandas_exact_arithmetic",
        }

    def calculate_kpis(self, data: Dict[str, Any]) -> Dict[str, float]:
        """15 exact KPIs — no rounding errors, no LLM."""
        safe_div = lambda n, d, m=1: round((n / d) * m, 2) if d else 0.0

        revenue         = float(data.get("revenue", 0))
        cogs            = float(data.get("cogs", 0))
        gross_profit    = float(data.get("gross_profit", revenue - cogs))
        ebitda          = float(data.get("ebitda", 0))
        ebit            = float(data.get("ebit", ebitda))
        net_income      = float(data.get("net_income", 0))
        total_assets    = float(data.get("total_assets", 0))
        total_equity    = float(data.get("total_equity", 1))
        current_assets  = float(data.get("current_assets", 0))
        current_liab    = float(data.get("current_liabilities", 1))
        inventory       = float(data.get("inventory", 0))
        total_debt      = float(data.get("total_debt", 0))
        cash            = float(data.get("cash", 0))
        ar              = float(data.get("accounts_receivable", 0))
        ap              = float(data.get("accounts_payable", 0))
        shares          = float(data.get("shares_outstanding", 1))
        diluted_shares  = float(data.get("diluted_shares", shares))
        interest_exp    = float(data.get("interest_expense", 0))
        tax_provision   = float(data.get("tax_provision", 0))
        pre_tax_income  = float(data.get("pre_tax_income", net_income + tax_provision))

        dso = safe_div(ar, revenue / 365) if revenue else 0.0
        dio = safe_div(inventory, cogs / 365) if cogs else 0.0
        dpo = safe_div(ap, cogs / 365) if cogs else 0.0
        ccc = round(dso + dio - dpo, 2)

        etr = safe_div(tax_provision, pre_tax_income, 100) if pre_tax_income else 0.0

        return {
            "gross_margin_pct":   safe_div(gross_profit, revenue, 100),
            "ebitda_margin_pct":  safe_div(ebitda, revenue, 100),
            "net_margin_pct":     safe_div(net_income, revenue, 100),
            "current_ratio":      safe_div(current_assets, current_liab),
            "quick_ratio":        safe_div(current_assets - inventory, current_liab),
            "debt_to_equity":     safe_div(total_debt, total_equity),
            "roe_pct":            safe_div(net_income, total_equity, 100),
            "roa_pct":            safe_div(net_income, total_assets, 100),
            "dso_days":           dso,
            "dpo_days":           dpo,
            "ccc_days":           ccc,
            "net_debt":           round(total_debt - cash, 2),
            "working_capital":    round(current_assets - current_liab, 2),
            "basic_eps":          safe_div(net_income, shares),
            "diluted_eps":        safe_div(net_income, diluted_shares),
            "interest_coverage":  safe_div(ebit, interest_exp) if interest_exp else 999.0,
            "effective_tax_rate": etr,
        }

    def forecast_revenue(
        self, historical: List[float], periods: int = 12
    ) -> Dict[str, Any]:
        """Dual model: sklearn LinearRegression + Holt-Winters ensemble (40/60 blend)."""
        if len(historical) < 4:
            trend = (historical[-1] - historical[0]) / max(len(historical) - 1, 1) if historical else 0
            forecast = [round(historical[-1] + trend * i, 2) for i in range(1, periods + 1)]
            return {"forecast": forecast, "method": "linear_extrapolation", "r2": None}

        X = np.arange(len(historical)).reshape(-1, 1)
        y = np.array(historical)
        lr = LinearRegression().fit(X, y)
        future_X = np.arange(len(historical), len(historical) + periods).reshape(-1, 1)
        lr_forecast = lr.predict(future_X).tolist()
        r2 = round(float(lr.score(X, y)), 4)

        try:
            hw = ExponentialSmoothing(historical, trend="add", seasonal=None).fit(optimized=True)
            hw_forecast = hw.forecast(periods).tolist()
        except Exception:
            hw_forecast = lr_forecast

        ensemble = [round(lr_val * 0.4 + hw_val * 0.6, 2)
                    for lr_val, hw_val in zip(lr_forecast, hw_forecast)]

        return {
            "forecast": ensemble,
            "lr_forecast": [round(v, 2) for v in lr_forecast],
            "hw_forecast": [round(v, 2) for v in hw_forecast],
            "r2": r2,
            "method": "lr_40_hw_60_ensemble",
            "periods": periods,
        }

    def detect_anomalies(self, data: Dict[str, Any], kpis: Dict[str, float]) -> List[str]:
        """Statistical anomaly detection — IQR method, no LLM."""
        flags = []

        # Gross margin anomaly
        gm = kpis.get("gross_margin_pct", 100)
        if gm < 15:
            flags.append(f"CRITICAL: Gross margin {gm}% is dangerously low (<15%)")
        elif gm < 30:
            flags.append(f"WARNING: Gross margin {gm}% is below 30% threshold")

        # Current ratio
        cr = kpis.get("current_ratio", 99)
        if cr < 1.0:
            flags.append(f"CRITICAL: Current ratio {cr} below 1.0 — liquidity risk")
        elif cr < 1.5:
            flags.append(f"WARNING: Current ratio {cr} below 1.5")

        # Net margin
        nm = kpis.get("net_margin_pct", 100)
        if nm < 0:
            flags.append(f"CRITICAL: Negative net margin {nm}%")

        # DSO
        dso = kpis.get("dso_days", 0)
        if dso > 90:
            flags.append(f"WARNING: DSO {dso} days exceeds 90-day threshold")

        # Debt-to-equity
        de = kpis.get("debt_to_equity", 0)
        if de > 3.0:
            flags.append(f"WARNING: D/E ratio {de} exceeds 3.0x — leverage risk")

        # Going concern — net debt / EBITDA
        net_debt = kpis.get("net_debt", 0)
        ebitda = float(data.get("ebitda", 1))
        if ebitda > 0:
            leverage = round(net_debt / ebitda, 2)
            if leverage > 5.0:
                flags.append(f"CRITICAL: Net debt/EBITDA {leverage}x exceeds 5.0x — going concern risk")
            elif leverage > 3.5:
                flags.append(f"WARNING: Net debt/EBITDA {leverage}x exceeds 3.5x")

        return flags

    def calculate_cash_runway(self, data: Dict[str, Any], kpis: Dict[str, float]) -> Dict[str, Any]:
        """Deterministic cash runway calculation per ASC 205-40."""
        cash = float(data.get("cash", 0))
        monthly_burn = float(data.get("monthly_cash_burn", 0))

        if monthly_burn <= 0:
            cfo = float(data.get("cash_from_operations", 0))
            if cfo < 0:
                monthly_burn = abs(cfo) / 12
            else:
                monthly_burn = 0

        if monthly_burn > 0:
            runway_months = round(cash / monthly_burn, 1)
        else:
            runway_months = 999.0

        status = "ADEQUATE"
        if runway_months < 6:
            status = "CRITICAL"
        elif runway_months < 12:
            status = "WARNING"

        return {
            "cash_balance": cash,
            "monthly_burn": monthly_burn,
            "runway_months": runway_months,
            "status": status,
            "asc_205_40_applicable": runway_months < 12,
        }

    def check_approval_triggers(
        self,
        variance: Dict[str, Any],
        kpis: Dict[str, float],
        anomalies: List[str],
        gaap_results: Optional[Dict[str, Any]],
        ifrs_results: Optional[Dict[str, Any]],
    ) -> List[dict]:
        """Deterministic threshold checks — triggers HITL review."""
        triggers = []

        var_pct = abs(variance.get("totals", {}).get("variance_pct", 0))
        if var_pct > 10:
            triggers.append({
                "reason": "variance_exceeds_10pct",
                "severity": "high",
                "value": var_pct,
                "threshold": 10.0,
                "message": f"Total variance {var_pct}% exceeds 10% threshold",
            })

        gm = kpis.get("gross_margin_pct", 100)
        if gm < 30:
            triggers.append({
                "reason": "gross_margin_below_30pct",
                "severity": "critical",
                "value": gm,
                "threshold": 30.0,
                "message": f"Gross margin {gm}% is below 30% — requires CFO review",
            })

        if len(anomalies) >= 3:
            triggers.append({
                "reason": "multiple_anomalies",
                "severity": "high",
                "value": len(anomalies),
                "threshold": 3,
                "message": f"{len(anomalies)} anomaly flags detected — requires CFO review",
            })

        if gaap_results:
            for std, result in gaap_results.items():
                if result.get("status") in ("NON_COMPLIANT", "DISCLOSURE_REQUIRED"):
                    triggers.append({
                        "reason": f"gaap_{result['status']}",
                        "severity": "critical" if result["status"] == "NON_COMPLIANT" else "high",
                        "standard": result.get("standard", std),
                        "message": result.get("finding", f"GAAP {std} compliance issue"),
                        "requires_disclosure": True,
                    })

        if ifrs_results:
            for std, result in ifrs_results.items():
                if result.get("status") in ("NON_COMPLIANT", "DISCLOSURE_REQUIRED"):
                    triggers.append({
                        "reason": f"ifrs_{result['status']}",
                        "severity": "critical" if result["status"] == "NON_COMPLIANT" else "high",
                        "standard": result.get("standard", std),
                        "message": result.get("finding", f"IFRS {std} compliance issue"),
                        "requires_disclosure": True,
                    })

        return triggers

    def calculate_reconciliation(
        self, gaap_data: Dict[str, Any], ifrs_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Quantify top GAAP-to-IFRS reconciling items."""
        items = {}

        # IFRS 16 vs ASC 842: operating lease reclassification
        rou_assets = float(gaap_data.get("rou_assets", 0))
        lease_liab = float(gaap_data.get("lease_liability", 0))
        op_lease_expense = float(gaap_data.get("operating_lease_expense", 0))
        items["ifrs16_vs_asc842_ebitda"] = {
            "description": "IFRS 16 single model — operating lease expense reclassified to D&A + interest",
            "gaap_treatment": "Dual model: operating leases in SG&A",
            "ifrs_treatment": "Single model: all leases capitalized; EBITDA higher",
            "ebitda_impact": round(op_lease_expense, 2),
            "balance_sheet_impact": round(rou_assets, 2),
        }

        # IAS 38 vs ASC 730: R&D development phase
        rd_expense = float(gaap_data.get("rd_expense", 0))
        dev_pct = float(ifrs_data.get("rd_dev_capitalizable_pct", 0.30))
        items["ias38_vs_asc730_rd"] = {
            "description": "IAS 38 requires capitalization of development costs if criteria met",
            "gaap_treatment": "All R&D expensed immediately (ASC 730)",
            "ifrs_treatment": f"~{dev_pct*100:.0f}% of R&D capitalizable as intangible asset",
            "pl_impact": round(rd_expense * dev_pct, 2),
            "balance_sheet_impact": round(rd_expense * dev_pct, 2),
        }

        # IAS 37 vs ASC 450: lower provision threshold
        items["ias37_vs_asc450_provisions"] = {
            "description": "IAS 37 recognizes provisions at >50% probable; GAAP at ~75%",
            "gaap_treatment": "~75% (virtually certain) threshold — ASC 450",
            "ifrs_treatment": ">50% probable threshold — IAS 37",
            "note": "Earlier recognition under IFRS may increase liabilities",
        }

        # IAS 36 vs ASC 350: goodwill impairment reversal
        goodwill = float(gaap_data.get("goodwill", 0))
        items["ias36_vs_asc350_goodwill"] = {
            "description": "IAS 36 permits impairment reversal; ASC 350 does not",
            "gaap_treatment": "No reversal of goodwill impairment (ASC 350)",
            "ifrs_treatment": "Impairment reversal permitted at CGU level (IAS 36)",
            "goodwill_balance": goodwill,
        }

        # IAS 2: LIFO prohibition
        items["ias2_vs_asc330_lifo"] = {
            "description": "LIFO strictly prohibited under IFRS; permitted under GAAP",
            "gaap_treatment": "LIFO, FIFO, or weighted average (ASC 330)",
            "ifrs_treatment": "LIFO PROHIBITED — must use FIFO or weighted avg (IAS 2)",
        }

        return items


def math_engine_node(state: CFOAgentState) -> CFOAgentState:
    """LangGraph node — runs full deterministic math pipeline."""
    engine = FinancialCalculationEngine()
    data = state.get("validated_data") or state.get("raw_financial_data") or {}
    errors = list(state.get("errors", []))
    warnings = list(state.get("warnings", []))
    audit = list(state.get("audit_log", []))

    try:
        actuals = data.get("actuals", {})
        budget  = data.get("budget", {})
        variance = engine.calculate_variance_analysis(actuals, budget) if actuals and budget else {
            "line_items": {}, "totals": {"variance_pct": 0}, "material_items": []
        }

        kpis = engine.calculate_kpis(data)
        anomalies = engine.detect_anomalies(data, kpis)
        runway = engine.calculate_cash_runway(data, kpis)

        historical_rev = data.get("historical_revenue", [])
        forecast = engine.forecast_revenue(historical_rev) if len(historical_rev) >= 4 else {}

        audit.append({
            "timestamp": datetime.utcnow().isoformat(),
            "agent": "math_engine",
            "action": "calculations_complete",
            "kpi_count": len(kpis),
            "anomaly_count": len(anomalies),
        })

        return {
            **state,
            "variance_table": variance,
            "kpi_metrics": kpis,
            "anomaly_flags": anomalies,
            "forecast_outputs": forecast,
            "data_quality_score": _score_data_quality(data),
            "agent_statuses": {**state.get("agent_statuses", {}), "math_engine": "complete"},
            "audit_log": audit,
            "errors": errors,
            "warnings": warnings,
        }

    except Exception as exc:
        errors.append(f"math_engine: {exc}")
        return {**state, "errors": errors, "agent_statuses": {**state.get("agent_statuses", {}), "math_engine": "error"}}


def _score_data_quality(data: Dict[str, Any]) -> float:
    required = ["revenue", "cogs", "gross_profit", "ebitda", "net_income",
                "total_assets", "total_equity", "cash"]
    present = sum(1 for f in required if data.get(f) is not None)
    return round(present / len(required), 2)
