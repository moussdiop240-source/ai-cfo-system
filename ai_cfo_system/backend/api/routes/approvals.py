import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...database.session import get_db_dep
from ...database.models import Task, Approval

router = APIRouter(prefix="/approvals", tags=["approvals"])


class ApprovalDecision(BaseModel):
    decision:    str   # "approved" | "rejected"
    feedback:    str
    approved_by: str


@router.get("/pending")
def get_pending_approvals(db: Session = Depends(get_db_dep)):
    """Return all tasks awaiting CFO approval."""
    tasks = db.query(Task).filter(Task.status == "awaiting_approval").all()
    return [
        {
            "task_id": t.id,
            "company_name": t.company_name,
            "period": t.period,
            "submitted_by": t.submitted_by,
            "submitted_at": t.submitted_at,
            "kpi_snapshot": {
                k: v for k, v in (t.kpi_metrics or {}).items()
                if k in ("gross_margin_pct", "ebitda_margin_pct", "net_margin_pct", "current_ratio")
            },
            "approval_triggers": [
                a.triggers for a in db.query(Approval)
                .filter(Approval.task_id == t.id, Approval.status == "pending")
                .all()
            ],
        }
        for t in tasks
    ]


@router.post("/{task_id}")
def submit_approval(
    task_id: str,
    body: ApprovalDecision,
    db: Session = Depends(get_db_dep),
):
    """CFO submits approval or rejection."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    if task.status not in ("awaiting_approval", "running"):
        raise HTTPException(
            status_code=422,
            detail=f"Task is in status '{task.status}' — cannot approve/reject",
        )

    if body.decision not in ("approved", "rejected"):
        raise HTTPException(status_code=422, detail="decision must be 'approved' or 'rejected'")

    # Create approval record
    approval = Approval(
        id=str(uuid.uuid4()),
        task_id=task_id,
        status=body.decision,
        decision=body.decision,
        feedback=body.feedback,
        approved_by=body.approved_by,
        decided_at=datetime.utcnow(),
    )
    db.add(approval)

    # Update task status
    task.status = "running"  # Pipeline will resume
    task.updated_at = datetime.utcnow()
    db.commit()

    # Note: In a full LangGraph HITL implementation, this would resume the graph
    # by updating the checkpoint state with human_decision=body.decision
    return {
        "task_id": task_id,
        "decision": body.decision,
        "approved_by": body.approved_by,
        "message": f"Task {task_id} {body.decision} by {body.approved_by}. Pipeline will resume.",
    }
