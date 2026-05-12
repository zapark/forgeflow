from sqlmodel import SQLModel, Session, create_engine

from app.models.audit import AuditLog
from app.models.task import Task, TaskStatus
from app.services.task_service import TaskService


def make_session():
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_task_control_pause_writes_allow_audit():
    with make_session() as session:
        task = Task(title="demo", goal_text="goal")
        session.add(task)
        session.commit()
        session.refresh(task)

        svc = TaskService(session)
        result = svc.control_task(task.id, "pause", actor="owner", reason="manual check")

        assert result is not None
        assert result.status == TaskStatus.WAITING_HUMAN

        audits = session.query(AuditLog).all()
        assert len(audits) == 1
        assert audits[0].decision == "ALLOW"
        assert audits[0].action == "task.pause"
