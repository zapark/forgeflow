from pydantic import BaseModel


class ExecutionStartResponse(BaseModel):
    workflow_run_id: int
    status: str


class CheckpointApprove(BaseModel):
    approved_by: str
    comment: str | None = None
