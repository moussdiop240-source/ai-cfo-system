"""
LangGraph Supervisor — routes between agents using conditional edges.
Deterministic routing based on state completeness flags.
"""
import os
from typing import Literal
from datetime import datetime

from langgraph.graph import StateGraph, END
try:
    from langgraph.checkpoint.memory import MemorySaver
except ImportError:
    MemorySaver = None

from .state import CFOAgentState
from .data_agent import data_agent_node
from .math_engine import math_engine_node
from .rag_agent import rag_agent_node
from .gaap_agent import gaap_agent_node
from .ifrs_agent import ifrs_agent_node
from .analysis_agent import analysis_agent_node
from .human_loop_node import human_review_node, compute_approval_triggers
from .reporting_agent import reporting_agent_node
from .debate_agent import debate_agent_node

SUPERVISOR_SYSTEM = """You are the supervisor of a CFO AI pipeline. Your only job is to route
to the correct next agent. Respond with exactly one word.

ROUTING RULES (apply in order):
1. If data not validated → data_agent
2. If math not calculated → math_engine
3. If RAG not retrieved → rag_agent
4. If GAAP not checked → gaap_agent
5. If IFRS not checked → ifrs_agent
6. If analysis not complete → analysis_agent
7. If requires_human_approval=True and not yet approved → human_review
8. If report not generated AND (no approval required OR approved) → reporting_agent
9. If report complete → end

Respond with EXACTLY ONE WORD:
data_agent | math_engine | rag_agent | gaap_agent | ifrs_agent |
analysis_agent | human_review | reporting_agent | end"""


def route_from_supervisor(
    state: CFOAgentState,
) -> Literal[
    "data_agent", "math_engine", "rag_agent", "gaap_agent",
    "ifrs_agent", "analysis_agent", "human_review",
    "reporting_agent", "__end__"
]:
    """
    DETERMINISTIC routing — no LLM used.
    Follows 9-step priority order from spec.
    """
    statuses = state.get("agent_statuses") or {}
    errors   = state.get("errors") or []

    # Hard stop if too many errors
    if len(errors) > 5:
        return "__end__"

    # 1. Data validation
    if not state.get("validated_data") or statuses.get("data_agent") not in ("complete",):
        return "data_agent"

    # 2. Math engine
    if not state.get("kpi_metrics") or statuses.get("math_engine") not in ("complete",):
        return "math_engine"

    # 3. RAG retrieval
    if not state.get("rag_chunks") or statuses.get("rag_agent") not in ("complete",):
        return "rag_agent"

    # 4. GAAP check
    if not state.get("gaap_results") or statuses.get("gaap_agent") not in ("complete",):
        return "gaap_agent"

    # 5. IFRS check
    if not state.get("ifrs_results") or statuses.get("ifrs_agent") not in ("complete",):
        return "ifrs_agent"

    # 6. Analysis
    if not state.get("analysis_narrative") or statuses.get("analysis_agent") not in ("complete",):
        return "analysis_agent"

    # 7. HITL — compute triggers then check
    # Compute triggers if not done yet
    if state.get("approval_triggers") is None:
        state_updated = compute_approval_triggers(state)
        if state_updated.get("requires_human_approval") and state.get("human_decision") != "approved":
            return "human_review"

    if state.get("requires_human_approval") and state.get("human_decision") not in ("approved",):
        return "human_review"

    # 8. Reporting
    if not state.get("final_report") or statuses.get("reporting_agent") not in ("complete",):
        return "reporting_agent"

    # 9. Done
    return "__end__"


def supervisor_node(state: CFOAgentState) -> CFOAgentState:
    """Supervisor node — records routing decision."""
    next_agent = route_from_supervisor(state)

    audit = list(state.get("audit_log", []))
    audit.append({
        "timestamp": datetime.utcnow().isoformat(),
        "agent": "supervisor",
        "action": "routing",
        "next": next_agent,
        "iteration": state.get("iteration_count", 0),
    })

    return {
        **state,
        "current_agent": "supervisor",
        "next_agent": next_agent,
        "iteration_count": state.get("iteration_count", 0) + 1,
        "agent_history": [*state.get("agent_history", []), "supervisor"],
        "audit_log": audit,
    }


def build_cfo_graph(db_dsn: str = None):
    """Build the full CFO LangGraph pipeline."""
    workflow = StateGraph(CFOAgentState)

    # Register all nodes
    workflow.add_node("supervisor",      supervisor_node)
    workflow.add_node("data_agent",      data_agent_node)
    workflow.add_node("math_engine",     math_engine_node)
    workflow.add_node("rag_agent",       rag_agent_node)
    workflow.add_node("gaap_agent",      gaap_agent_node)
    workflow.add_node("ifrs_agent",      ifrs_agent_node)
    workflow.add_node("analysis_agent",  analysis_agent_node)
    workflow.add_node("human_review",    human_review_node)
    workflow.add_node("reporting_agent", reporting_agent_node)
    workflow.add_node("debate_agent",    debate_agent_node)

    # Entry point
    workflow.set_entry_point("supervisor")

    # Conditional routing from supervisor
    workflow.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "data_agent":      "data_agent",
            "math_engine":     "math_engine",
            "rag_agent":       "rag_agent",
            "gaap_agent":      "gaap_agent",
            "ifrs_agent":      "ifrs_agent",
            "analysis_agent":  "analysis_agent",
            "human_review":    "human_review",
            "reporting_agent": "reporting_agent",
            "__end__":         END,
        },
    )

    # All agents loop back to supervisor
    for agent in [
        "data_agent", "math_engine", "rag_agent", "gaap_agent",
        "ifrs_agent", "analysis_agent", "reporting_agent",
    ]:
        workflow.add_edge(agent, "supervisor")

    workflow.add_edge("human_review", "supervisor")
    workflow.add_edge("debate_agent", END)  # Debate is called independently

    # Checkpointing
    checkpointer = MemorySaver() if MemorySaver else None

    compile_kwargs = {}
    if checkpointer:
        compile_kwargs["checkpointer"] = checkpointer
        compile_kwargs["interrupt_before"] = ["human_review"]

    return workflow.compile(**compile_kwargs)


def create_initial_state(
    task_id: str,
    task_type: str,
    task_description: str,
    company_name: str,
    period: str,
    raw_financial_data: dict,
    submitted_by: str = "system",
    report_format: str = "board",
) -> CFOAgentState:
    """Create a clean initial state for a new pipeline run."""
    from datetime import datetime
    return CFOAgentState(
        task_id=task_id,
        task_type=task_type,
        task_description=task_description,
        company_name=company_name,
        period=period,
        report_format=report_format,
        submitted_by=submitted_by,
        submitted_at=datetime.utcnow().isoformat(),
        raw_financial_data=raw_financial_data,
        raw_documents=None,
        math_results=None,
        variance_table=None,
        kpi_metrics=None,
        forecast_outputs=None,
        reconciliation_data=None,
        data_quality_score=None,
        anomaly_flags=None,
        gaap_results=None,
        ifrs_results=None,
        gaap_compliant_count=None,
        gaap_issues_count=None,
        ifrs_compliant_count=None,
        ifrs_issues_count=None,
        validated_data=None,
        schema_errors=None,
        schema_version=None,
        structured_output=None,
        rag_chunks=None,
        rag_query_used=None,
        rag_sources_cited=None,
        retrieval_confidence=None,
        analysis_narrative=None,
        identified_risks=None,
        opportunities=None,
        action_items=None,
        ai_confidence_score=None,
        debate_ifrs_advocate=None,
        debate_gaap_advocate=None,
        debate_arbiter=None,
        debate_complete=False,
        requires_human_approval=False,
        approval_triggers=None,
        human_decision=None,
        human_feedback=None,
        approved_by=None,
        approved_at=None,
        draft_report=None,
        final_report=None,
        report_pdf_path=None,
        current_agent="supervisor",
        next_agent=None,
        agent_history=[],
        iteration_count=0,
        max_iterations=20,
        agent_statuses={},
        errors=[],
        warnings=[],
        flags=[],
        audit_log=[],
        total_tokens_used=0,
        total_cost_usd=0.0,
        processing_time_ms=0,
    )
