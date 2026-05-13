from typing import Any

from pydantic import BaseModel, Field


class ResourceLimit(BaseModel):
    timeout_sec: int = Field(default=30, ge=1)
    memory_mb: int = Field(default=256, ge=1)
    cpu_quota: float = Field(default=0.5, gt=0)


class ToolSpec(BaseModel):
    tool_name: str
    version: str = "0.1.0"
    permissions: list[str] = Field(default_factory=list)
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    resource_limit: ResourceLimit = Field(default_factory=ResourceLimit)
    allowed_domains: list[str] = Field(default_factory=list)
    risk_level: str = "low"


class ToolExecuteRequest(BaseModel):
    tool: ToolSpec
    input: dict[str, Any] = Field(default_factory=dict)
    actor: str = "system"


class ToolExecuteResponse(BaseModel):
    status: str
    tool_run_id: int | None = None
    workflow_run_id: int
    event_type: str
    reason: str | None = None
    output: dict[str, Any] | None = None
