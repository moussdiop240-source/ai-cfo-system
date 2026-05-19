"""
IFRS Agent — deterministic 12 IASB standard checks. ZERO LLM.
"""
from datetime import datetime
from .state import CFOAgentState
from ..compliance.ifrs_engine import IFRSEngine
from ..agents.math_engine import FinancialCalculationEngine


def ifrs_agent_node(state: CFOAgentState) -> CFOAgentState:
    """LangGraph node — runs all 12 IFRS checks deterministically."""
    errors = list(state.get("errors", []))
    audit  = list(state.get("audit_log", []))

    data     = state.get("validated_data") or state.get("raw_financial_data") or {}
    kpis     = state.get("kpi_metrics") or {}
    variance = state.get("variance_table") or {"totals": {"variance_pct": 0}, "line_items": {}, "material_items": []}

    math_engine = FinancialCalculationEngine()
    runway = math_engine.calculate_cash_runway(data, kpis)

    ifrs = IFRSEngine()
    results = ifrs.check_all(data, kpis, variance, runway)

    compliant  = sum(1 for r in results.values() if r["status"] == "COMPLIANT")
    disclosure = sum(1 for r in results.values() if r["status"] == "DISCLOSURE_REQUIRED")
    non_comp   = sum(1 for r in results.values() if r["status"] == "NON_COMPLIANT")

    audit.append({
        "timestamp": datetime.utcnow().isoformat(),
        "agent": "ifrs_agent",
        "action": "ifrs_checks_complete",
        "compliant": compliant,
        "disclosure_required": disclosure,
        "non_compliant": non_comp,
    })

    return {
        **state,
        "ifrs_results": results,
        "ifrs_compliant_count": compliant,
        "ifrs_issues_count": disclosure + non_comp,
        "agent_statuses": {**state.get("agent_statuses", {}), "ifrs_agent": "complete"},
        "audit_log": audit,
        "errors": errors,
    }
