from fastapi import APIRouter, HTTPException

from app.core.db import get_session
from app.schemas.tool import ToolExecuteRequest, ToolExecuteResponse
from app.services.tool_runtime_service import ToolRuntimeService

router = APIRouter(tags=["tools"])


@router.post("/workflow-runs/{workflow_run_id}/tools/execute", response_model=ToolExecuteResponse)
def execute_tool(workflow_run_id: int, payload: ToolExecuteRequest):
    with get_session() as session:
        result = ToolRuntimeService(session).execute(
            workflow_run_id,
            payload.tool,
            payload.input,
            payload.actor,
        )
    if result is None:
        raise HTTPException(status_code=404, detail="workflow run not found")
    return result
