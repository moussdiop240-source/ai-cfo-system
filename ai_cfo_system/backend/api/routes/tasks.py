import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...agents.supervisor import build_cfo_graph, create_initial_state
from ...database.models import Task
from ...database.session import get_db_dep

router = APIRouter(prefix="/tasks", tags=["tasks"])

# Shared graph instance (thread-safe — LangGraph handles concurrency)
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_cfo_graph()
    return _graph


class TaskRequest(BaseModel):
    task_type:         str   = "full_report"
    task_description:  str
    company_name:      str
    period:            str
    report_format:     str   = "board"
    submitted_by:      str   = "api_user"
    raw_financial_data: dict


class TaskResponse(BaseModel):
    task_id:  str
    status:   str
    message:  str


async def _run_pipeline(task_id: str, initial_state: dict, db: Session):
    """Run the LangGraph pipeline in background and persist results."""
    graph = get_graph()
    try:
        config = {"configurable": {"thread_id": task_id}}
        final_state = graph.invoke(initial_state, config=config)

        # Persist to DB
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status              = "complete" if not final_state.get("errors") else "error"
            task.kpi_metrics         = final_state.get("kpi_metrics")
            task.variance_table      = final_state.get("variance_table")
            task.gaap_results        = final_state.get("gaap_results")
            task.ifrs_results        = final_state.get("ifrs_results")
            task.analysis_narrative  = final_state.get("analysis_narrative")
            task.final_report        = final_state.get("final_report")
            task.audit_log           = final_state.get("audit_log")
            task.errors              = final_state.get("errors")
            task.total_tokens_used   = final_state.get("total_tokens_used", 0)
            task.processing_time_ms  = final_state.get("processing_time_ms", 0)
            task.updated_at          = datetime.utcnow()
            db.commit()

    except Exception as exc:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = "error"
            task.errors = [str(exc)]
            db.commit()


@router.post("", response_model=TaskResponse, status_code=202)
async def create_task(
    request: TaskRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_dep),
):
    task_id = str(uuid.uuid4())

    # Create DB record
    task = Task(
        id=task_id,
        task_type=request.task_type,
        description=request.task_description,
        company_name=request.company_name,
        period=request.period,
        report_format=request.report_format,
        submitted_by=request.submitted_by,
        status="running",
    )
    db.add(task)
    db.commit()

    # Build initial state
    initial_state = create_initial_state(
        task_id=task_id,
        task_type=request.task_type,
        task_description=request.task_description,
        company_name=request.company_name,
        period=request.period,
        raw_financial_data=request.raw_financial_data,
        submitted_by=request.submitted_by,
        report_format=request.report_format,
    )

    # Run pipeline in background
    background_tasks.add_task(_run_pipeline, task_id, initial_state, db)

    return TaskResponse(
        task_id=task_id,
        status="running",
        message="Pipeline started. Poll GET /tasks/{task_id} for results.",
    )


@router.get("/{task_id}")
def get_task(task_id: str, db: Session = Depends(get_db_dep)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return {
        "task_id": task.id,
        "status": task.status,
        "company_name": task.company_name,
        "period": task.period,
        "submitted_at": task.submitted_at,
        "updated_at": task.updated_at,
        "kpi_metrics": task.kpi_metrics,
        "gaap_issues": sum(
            1 for r in (task.gaap_results or {}).values()
            if r.get("status") != "COMPLIANT"
        ),
        "ifrs_issues": sum(
            1 for r in (task.ifrs_results or {}).values()
            if r.get("status") != "COMPLIANT"
        ),
        "has_report": bool(task.final_report),
        "errors": task.errors or [],
    }


@router.get("/{task_id}/report")
def get_report(task_id: str, db: Session = Depends(get_db_dep)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    if not task.final_report:
        raise HTTPException(status_code=425, detail="Report not yet generated")

    return {
        "task_id": task_id,
        "company_name": task.company_name,
        "period": task.period,
        "report_format": task.report_format,
        "report": task.final_report,
        "kpi_metrics": task.kpi_metrics,
        "gaap_results": task.gaap_results,
        "ifrs_results": task.ifrs_results,
    }
