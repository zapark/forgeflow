from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ForgeFlow API"
    app_version: str = "0.1.0"

    database_url: str = "sqlite:///./forgeflow.db"

    default_created_by: str = "system"
    default_workflow_spec_version: str = "1.0.0"
    default_workflow_start_node: str = "planner_start"

    allowed_task_actions: str = "pause,resume,cancel"
    timeline_default_limit: int = Field(default=50, ge=1, le=500)
    timeline_max_limit: int = Field(default=200, ge=1, le=1000)

    @property
    def allowed_task_actions_set(self) -> set[str]:
        return {x.strip() for x in self.allowed_task_actions.split(",") if x.strip()}


settings = Settings()
