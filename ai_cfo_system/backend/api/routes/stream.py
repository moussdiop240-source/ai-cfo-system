import asyncio
import json
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ...database.session import get_db_dep
from ...database.models import Task

router = APIRouter(prefix="/tasks", tags=["stream"])


async def _task_event_generator(task_id: str, db: Session):
    """Server-Sent Events generator — polls task status every second."""
    max_polls = 300  # 5 minutes max
    for _ in range(max_polls):
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            yield f"data: {json.dumps({'error': 'task_not_found'})}\n\n"
            return

        payload = {
            "task_id": task_id,
            "status": task.status,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        }

        if task.status in ("complete", "error"):
            payload["final_report"] = task.final_report
            payload["errors"] = task.errors or []
            yield f"data: {json.dumps(payload)}\n\n"
            return

        yield f"data: {json.dumps(payload)}\n\n"
        await asyncio.sleep(1)

    yield f"data: {json.dumps({'error': 'stream_timeout'})}\n\n"


@router.get("/{task_id}/stream")
async def stream_task(task_id: str, db: Session = Depends(get_db_dep)):
    """SSE endpoint — streams task progress until completion."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return StreamingResponse(
        _task_event_generator(task_id, db),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
