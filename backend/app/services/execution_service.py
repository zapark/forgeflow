import json
from datetime import datetime

from sqlmodel import Session, select

from app.models.task import Task, TaskStatus
from app.models.workflow import WorkflowEvent, WorkflowRun, WorkflowStatus


class ExecutionService:
    def __init__(self, session: Session):
        self.session = session

    def start_execution(self, task_id: int) -> WorkflowRun | None:
        task = self.session.get(Task, task_id)
        if task is None:
            return None

        task.status = TaskStatus.RUNNING
        task.updated_at = datetime.utcnow()
        run = WorkflowRun(task_id=task.id, status=WorkflowStatus.RUNNING)
        self.session.add(task)
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)

        self._event(run.id, "EXECUTION_STARTED", {"task_id": task_id})
        return run

    def timeline(self, task_id: int, event_type: str | None = None, limit: int = 50, offset: int = 0) -> list[WorkflowEvent]:
        runs = list(self.session.exec(select(WorkflowRun).where(WorkflowRun.task_id == task_id)))
        if not runs:
            return []
        run_ids = [r.id for r in runs if r.id is not None]
        query = select(WorkflowEvent).where(WorkflowEvent.workflow_run_id.in_(run_ids))
        if event_type:
            query = query.where(WorkflowEvent.event_type == event_type)
        query = query.order_by(WorkflowEvent.created_at).offset(offset).limit(limit)
        return list(self.session.exec(query))

    def approve_checkpoint(self, task_id: int, node_id: str, approved_by: str, comment: str | None) -> WorkflowRun | None:
        run = self.session.exec(
            select(WorkflowRun).where(WorkflowRun.task_id == task_id).order_by(WorkflowRun.id.desc())
        ).first()
        if run is None:
            return None

        run.status = WorkflowStatus.RUNNING
        run.current_node_id = node_id
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)

        self._event(
            run.id,
            "CHECKPOINT_APPROVED",
            {"node_id": node_id, "approved_by": approved_by, "comment": comment},
        )
        return run

    def _event(self, run_id: int, event_type: str, payload: dict) -> None:
        event = WorkflowEvent(
            workflow_run_id=run_id,
            event_type=event_type,
            payload_json=json.dumps(payload, ensure_ascii=False),
            trace_id=f"wf-{run_id}-{int(datetime.utcnow().timestamp())}",
        )
        self.session.add(event)
        self.session.commit()
