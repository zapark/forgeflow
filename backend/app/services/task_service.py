from datetime import datetime

from sqlmodel import Session, select

from app.core.config import settings
from app.models.audit import AuditLog
from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate


class TaskService:
    def __init__(self, session: Session):
        self.session = session

    def create_task(self, data: TaskCreate) -> Task:
        task = Task(title=data.title, goal_text=data.goal)
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def get_task(self, task_id: int) -> Task | None:
        return self.session.get(Task, task_id)

    ALLOWED_ACTIONS = settings.allowed_task_actions_set

    def control_task(self, task_id: int, action: str, actor: str = "user", reason: str | None = None) -> Task | None:
        task = self.get_task(task_id)
        if task is None:
            return None

        if action not in self.ALLOWED_ACTIONS:
            self._audit(actor, f"task.{action}", f"task:{task_id}", "DENY", "invalid action")
            return None

        if action == "pause":
            task.status = TaskStatus.WAITING_HUMAN
        elif action == "resume":
            task.status = TaskStatus.RUNNING
        elif action == "cancel":
            task.status = TaskStatus.CANCELED

        task.updated_at = datetime.utcnow()
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        self._audit(actor, f"task.{action}", f"task:{task_id}", "ALLOW", reason)
        return task

    def list_tasks(self) -> list[Task]:
        return list(self.session.exec(select(Task)))

    def _audit(self, actor: str, action: str, target: str, decision: str, reason: str | None) -> None:
        audit = AuditLog(actor=actor, action=action, target=target, decision=decision, reason=reason, trace_id=f"audit-{actor}")
        self.session.add(audit)
        self.session.commit()
