from sqlmodel import SQLModel, Session, create_engine

from app.models.audit import AuditLog
from app.models.system_setting import SystemSetting
from app.models.task import Task
from app.services.system_setting_service import SystemSettingService
from app.services.task_service import TaskService


def make_session():
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_task_control_rejects_invalid_action():
    with make_session() as session:
        task = Task(title="t", goal_text="g")
        session.add(task)
        session.commit()
        session.refresh(task)

        service = TaskService(session)
        result = service.control_task(task.id, "invalid", actor="tester")
        assert result is None

        audits = session.query(AuditLog).all()
        assert len(audits) == 1
        assert audits[0].decision == "DENY"


def test_setting_upsert_respects_editable_keys():
    with make_session() as session:
        svc = SystemSettingService(session)
        updated = svc.upsert_setting("ALLOWED_TASK_ACTIONS", "pause,resume", "admin")
        assert updated.value == "pause,resume"

        try:
            svc.upsert_setting("NOT_ALLOWED_KEY", "1", "admin")
            assert False, "should raise"
        except ValueError:
            assert True

        rows = session.query(SystemSetting).all()
        assert len(rows) == 1
