from typing import Any, Dict, List, Optional, TypedDict


class CFOAgentState(TypedDict):
    # Task Identity
    task_id:           str
    task_type:         str       # "variance_analysis" | "full_report" | "gaap_review"
    task_description:  str
    company_name:      str
    period:            str       # "Q1 2025"
    report_format:     str       # "board" | "investor" | "internal" | "audit"
    submitted_by:      str
    submitted_at:      str       # ISO timestamp

    # Raw Input
    raw_financial_data: Optional[Dict[str, Any]]
    raw_documents:      Optional[List[str]]

    # LAYER 1: Math Engine (DETERMINISTIC — NO LLM)
    math_results:        Optional[List[dict]]
    variance_table:      Optional[Dict[str, Any]]
    kpi_metrics:         Optional[Dict[str, float]]
    forecast_outputs:    Optional[Dict[str, Any]]
    reconciliation_data: Optional[Dict[str, Any]]
    data_quality_score:  Optional[float]
    anomaly_flags:       Optional[List[str]]

    # LAYER 1: Compliance (DETERMINISTIC — NO LLM)
    gaap_results:        Optional[Dict[str, Any]]
    ifrs_results:        Optional[Dict[str, Any]]
    gaap_compliant_count: Optional[int]
    gaap_issues_count:   Optional[int]
    ifrs_compliant_count: Optional[int]
    ifrs_issues_count:   Optional[int]

    # LAYER 2: Validated Schemas
    validated_data:      Optional[Dict[str, Any]]
    schema_errors:       Optional[List[str]]
    schema_version:      Optional[str]
    structured_output:   Optional[Dict[str, Any]]

    # LAYER 4: RAG Context
    rag_chunks:          Optional[List[dict]]
    rag_query_used:      Optional[str]
    rag_sources_cited:   Optional[List[str]]
    retrieval_confidence: Optional[float]

    # AI Analysis (interprets math — NEVER calculates)
    analysis_narrative:  Optional[str]
    identified_risks:    Optional[List[str]]
    opportunities:       Optional[List[str]]
    action_items:        Optional[List[str]]
    ai_confidence_score: Optional[float]

    # Debate Agent
    debate_ifrs_advocate:  Optional[str]
    debate_gaap_advocate:  Optional[str]
    debate_arbiter:        Optional[str]
    debate_complete:       bool

    # Human-in-the-Loop
    requires_human_approval: bool
    approval_triggers:       Optional[List[dict]]
    human_decision:          Optional[str]   # "approved"|"rejected"|"pending"
    human_feedback:          Optional[str]
    approved_by:             Optional[str]
    approved_at:             Optional[str]

    # Report
    draft_report:     Optional[str]
    final_report:     Optional[str]
    report_pdf_path:  Optional[str]

    # LangGraph Control
    current_agent:    str
    next_agent:       Optional[str]
    agent_history:    List[str]
    iteration_count:  int
    max_iterations:   int
    agent_statuses:   Dict[str, str]

    # Observability
    errors:          List[str]
    warnings:        List[str]
    flags:           List[str]
    audit_log:       List[dict]
    total_tokens_used: int
    total_cost_usd:    float
    processing_time_ms: int
