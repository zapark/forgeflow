from fastapi import FastAPI

from app.api.routes_executions import router as execution_router
from app.api.routes_settings import router as settings_router
from app.core.config import settings
from app.api.routes_tasks import router as task_router

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.include_router(task_router, prefix="/api/v1")
app.include_router(execution_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
