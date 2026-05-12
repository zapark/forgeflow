from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings
from app.models.audit import AuditLog
from app.models.system_setting import SystemSetting
from app.models.task import Task
from app.models.workflow import WorkflowEvent, WorkflowRun

engine = create_engine(settings.database_url, echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)
