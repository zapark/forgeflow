from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class WorkflowStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    WAITING_HUMAN = "WAITING_HUMAN"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class WorkflowRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(index=True)
    workflow_spec_version: str = Field(default="1.0.0")
    current_node_id: str = Field(default="planner_start")
    status: WorkflowStatus = Field(default=WorkflowStatus.CREATED)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: datetime | None = None


class WorkflowEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workflow_run_id: int = Field(index=True)
    event_type: str
    payload_json: str
    trace_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
