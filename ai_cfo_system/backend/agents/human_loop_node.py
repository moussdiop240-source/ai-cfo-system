"""
Human-in-the-Loop (HITL) node.
LangGraph interrupt_before=["human_review"] blocks the pipeline here
until a CFO submits a decision via POST /approvals/{task_id}.
"""
from datetime import datetime

from ..agents.math_engine import FinancialCalculationEngine
from .state import CFOAgentState

HITL_PROMPT = """Review required before report distribution.

Please confirm:
1. All variance explanations are accurate and complete
2. GAAP/IFRS disclosure requirements are addressed in your notes
3. Management action plan is approved
4. Report is authorized for {report_format} distribution

Your approval notes must include:
- Explanation of any flagged variances
- GAAP/IFRS disclosure plan (which footnote, which standard)
- Owner and deadline for each action item
"""


def human_review_node(state: CFOAgentState) -> CFOAgentState:
    """
    HITL interrupt node.
    LangGraph pauses pipeline BEFORE this node (interrupt_before=["human_review"]).
    When the graph is resumed with human_decision in state, this node records
    the decision and checks approval triggers.
    """
    audit  = list(state.get("audit_log", []))
    errors = list(state.get("errors", []))

    decision  = state.get("human_decision", "pending")
    feedback  = state.get("human_feedback", "")
    approved_by = state.get("approved_by", "")

    if decision == "approved":
        audit.append({
            "timestamp": datetime.utcnow().isoformat(),
            "agent": "human_review",
            "action": "approved",
            "approved_by": approved_by,
            "feedback": feedback,
        })
        return {
            **state,
            "requires_human_approval": False,
            "agent_statuses": {**state.get("agent_statuses", {}), "human_review": "approved"},
            "audit_log": audit,
        }

    elif decision == "rejected":
        audit.append({
            "timestamp": datetime.utcnow().isoformat(),
            "agent": "human_review",
            "action": "rejected",
            "approved_by": approved_by,
            "feedback": feedback,
        })
        errors.append(f"Human review rejected by {approved_by}: {feedback}")
        return {
            **state,
            "agent_statuses": {**state.get("agent_statuses", {}), "human_review": "rejected"},
            "audit_log": audit,
            "errors": errors,
        }

    else:
        # Still pending — stay in this node (pipeline is interrupted)
        audit.append({
            "timestamp": datetime.utcnow().isoformat(),
            "agent": "human_review",
            "action": "awaiting_decision",
            "triggers": state.get("approval_triggers", []),
        })
        return {
            **state,
            "human_decision": "pending",
            "agent_statuses": {**state.get("agent_statuses", {}), "human_review": "pending"},
            "audit_log": audit,
        }


def compute_approval_triggers(state: CFOAgentState) -> CFOAgentState:
    """Called by supervisor to check if HITL is needed."""
    engine = FinancialCalculationEngine()
    variance = state.get("variance_table") or {}
    kpis     = state.get("kpi_metrics") or {}
    anomalies = state.get("anomaly_flags") or []
    gaap     = state.get("gaap_results") or {}
    ifrs     = state.get("ifrs_results") or {}

    triggers = engine.check_approval_triggers(variance, kpis, anomalies, gaap, ifrs)
    needs_review = len(triggers) > 0

    return {
        **state,
        "requires_human_approval": needs_review,
        "approval_triggers": triggers,
    }
