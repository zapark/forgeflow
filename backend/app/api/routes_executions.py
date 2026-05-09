from fastapi import APIRouter, HTTPException

from app.core.db import get_session
from app.schemas.execution import CheckpointApprove, ExecutionStartResponse
from app.services.runtime_config_service import RuntimeConfigService
from app.services.execution_service import ExecutionService

router = APIRouter(tags=["executions"])


@router.post("/executions/{task_id}/start", response_model=ExecutionStartResponse)
def start_execution(task_id: int):
    with get_session() as session:
        run = ExecutionService(session).start_execution(task_id)
    if run is None:
        raise HTTPException(status_code=404, detail="task not found")
    return {"workflow_run_id": run.id, "status": run.status}


@router.get("/executions/{task_id}/timeline")
def get_timeline(task_id: int, event_type: str | None = None, limit: int | None = None, offset: int = 0):
    with get_session() as session:
        runtime_cfg = RuntimeConfigService(session)
        effective_limit = limit if limit is not None else runtime_cfg.timeline_default_limit()
        safe_limit = min(effective_limit, runtime_cfg.timeline_max_limit())
        timeline = ExecutionService(session).timeline(task_id, event_type=event_type, limit=safe_limit, offset=offset)
    return timeline


@router.post("/executions/{task_id}/checkpoint/{node_id}/approve")
def approve_checkpoint(task_id: int, node_id: str, payload: CheckpointApprove):
    with get_session() as session:
        run = ExecutionService(session).approve_checkpoint(task_id, node_id, payload.approved_by, payload.comment)
    if run is None:
        raise HTTPException(status_code=404, detail="workflow run not found")
    return {"workflow_run_id": run.id, "status": run.status, "current_node_id": run.current_node_id}
