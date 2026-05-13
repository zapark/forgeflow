import os
from pathlib import Path

from pydantic import Field
from pydantic import BaseModel, ConfigDict


class Settings(BaseModel):
    model_config = ConfigDict(extra="ignore")

    app_name: str = "ForgeFlow API"
    app_version: str = "0.1.0"

    database_url: str = "sqlite:///./forgeflow.db"

    default_created_by: str = "system"
    default_workflow_spec_version: str = "1.0.0"
    default_workflow_start_node: str = "planner_start"

    allowed_task_actions: str = "pause,resume,cancel"
    allowed_tool_permissions: str = "fs.read"
    checkpoint_tool_risk_levels: str = "high"
    timeline_default_limit: int = Field(default=50, ge=1, le=500)
    timeline_max_limit: int = Field(default=200, ge=1, le=1000)
    editable_setting_keys: str = (
        "ALLOWED_TASK_ACTIONS,ALLOWED_TOOL_PERMISSIONS,CHECKPOINT_TOOL_RISK_LEVELS,"
        "TIMELINE_DEFAULT_LIMIT,TIMELINE_MAX_LIMIT"
    )

    @property
    def allowed_task_actions_set(self) -> set[str]:
        return {x.strip() for x in self.allowed_task_actions.split(",") if x.strip()}

    @property
    def editable_setting_keys_set(self) -> set[str]:
        return {x.strip() for x in self.editable_setting_keys.split(",") if x.strip()}


def _env_values() -> dict[str, str]:
    fields = Settings.model_fields
    values = _dotenv_values(Path(".env"))
    values.update(os.environ)
    return {name: values[name.upper()] for name in fields if name.upper() in values}


def _dotenv_values(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


settings = Settings(**_env_values())
