from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from ...agents.debate_agent import debate_agent_node
from ...agents.supervisor import create_initial_state
import uuid

router = APIRouter(prefix="/debate", tags=["debate"])


class DebateRequest(BaseModel):
    company_name:      str
    period:            str
    financial_data:    Dict[str, Any]
    jurisdiction:      Optional[str] = "United States"
    listing_exchange:  Optional[str] = "NASDAQ"
    industry:          Optional[str] = "Technology"


@router.post("/run")
def run_debate(request: DebateRequest):
    """Run the 3-round IFRS vs GAAP agentic debate."""
    state = create_initial_state(
        task_id=str(uuid.uuid4()),
        task_type="debate",
        task_description="IFRS vs GAAP framework debate",
        company_name=request.company_name,
        period=request.period,
        raw_financial_data={
            **request.financial_data,
            "jurisdiction": request.jurisdiction,
            "listing_exchange": request.listing_exchange,
            "industry": request.industry,
        },
    )

    # Run math + compliance first to get deterministic inputs for debate
    from ...agents.math_engine import math_engine_node
    from ...agents.gaap_agent import gaap_agent_node
    from ...agents.ifrs_agent import ifrs_agent_node
    from ...agents.data_agent import data_agent_node

    state = data_agent_node(state)
    state = math_engine_node(state)
    state = gaap_agent_node(state)
    state = ifrs_agent_node(state)
    state = debate_agent_node(state)

    if state.get("errors"):
        raise HTTPException(status_code=500, detail=state["errors"])

    return {
        "company_name": request.company_name,
        "period": request.period,
        "round_1_ifrs_advocate": state.get("debate_ifrs_advocate"),
        "round_2_gaap_advocate": state.get("debate_gaap_advocate"),
        "round_3_arbiter_verdict": state.get("debate_arbiter"),
        "gaap_summary": {
            std: {"status": r["status"], "standard": r.get("standard", std)}
            for std, r in (state.get("gaap_results") or {}).items()
        },
        "ifrs_summary": {
            std: {"status": r["status"], "standard": r.get("standard", std)}
            for std, r in (state.get("ifrs_results") or {}).items()
        },
        "kpi_metrics": state.get("kpi_metrics"),
    }
