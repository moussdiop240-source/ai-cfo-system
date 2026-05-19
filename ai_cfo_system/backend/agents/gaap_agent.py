"""
GAAP Agent — deterministic 12 ASC standard checks. ZERO LLM.
"""
from datetime import datetime
from .state import CFOAgentState
from ..compliance.gaap_engine import GAAPEngine
from ..agents.math_engine import FinancialCalculationEngine


def gaap_agent_node(state: CFOAgentState) -> CFOAgentState:
    """LangGraph node — runs all 12 GAAP checks deterministically."""
    errors = list(state.get("errors", []))
    audit  = list(state.get("audit_log", []))

    data     = state.get("validated_data") or state.get("raw_financial_data") or {}
    kpis     = state.get("kpi_metrics") or {}
    variance = state.get("variance_table") or {"totals": {"variance_pct": 0}, "line_items": {}, "material_items": []}

    engine_math = FinancialCalculationEngine()
    runway = engine_math.calculate_cash_runway(data, kpis)

    gaap = GAAPEngine()
    results = gaap.check_all(data, kpis, variance, runway)

    compliant  = sum(1 for r in results.values() if r["status"] == "COMPLIANT")
    disclosure = sum(1 for r in results.values() if r["status"] == "DISCLOSURE_REQUIRED")
    non_comp   = sum(1 for r in results.values() if r["status"] == "NON_COMPLIANT")

    audit.append({
        "timestamp": datetime.utcnow().isoformat(),
        "agent": "gaap_agent",
        "action": "gaap_checks_complete",
        "compliant": compliant,
        "disclosure_required": disclosure,
        "non_compliant": non_comp,
    })

    return {
        **state,
        "gaap_results": results,
        "gaap_compliant_count": compliant,
        "gaap_issues_count": disclosure + non_comp,
        "agent_statuses": {**state.get("agent_statuses", {}), "gaap_agent": "complete"},
        "audit_log": audit,
        "errors": errors,
    }
