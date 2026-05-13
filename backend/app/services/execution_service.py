import json
from datetime import datetime

from sqlmodel import Session, select

from app.models.audit import AuditLog
from app.models.task import Task, TaskStatus
from app.models.workflow import RoleRun, ToolRun, WorkflowEvent, WorkflowRun, WorkflowStatus


class ExecutionService:
    def __init__(self, session: Session):
        self.session = session

    def start_execution(self, task_id: int) -> WorkflowRun | None:
        task = self.session.get(Task, task_id)
        if task is None:
            return None

        task.status = TaskStatus.PLANNING
        task.updated_at = datetime.utcnow()
        run = WorkflowRun(task_id=task.id, status=WorkflowStatus.RUNNING, current_node_id="planner_start")
        self.session.add(task)
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)

        self._event(run.id, "EXECUTION_STARTED", {"task_id": task_id})
        self._audit("system", "execution.start", f"task:{task_id}", "ALLOW", f"workflow_run:{run.id}")
        self._seed_mvp_workflow(task, run)

        task.status = TaskStatus.WAITING_HUMAN
        task.updated_at = datetime.utcnow()
        run.status = WorkflowStatus.WAITING_HUMAN
        run.current_node_id = "human_checkpoint"
        self.session.add(task)
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
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
        self._audit(approved_by, "checkpoint.approve", f"task:{task_id}", "ALLOW", comment)
        return run

    def replay(self, workflow_run_id: int) -> dict | None:
        run = self.session.get(WorkflowRun, workflow_run_id)
        if run is None:
            return None

        events = list(
            self.session.exec(
                select(WorkflowEvent)
                .where(WorkflowEvent.workflow_run_id == workflow_run_id)
                .order_by(WorkflowEvent.created_at)
            )
        )
        roles = list(
            self.session.exec(
                select(RoleRun).where(RoleRun.workflow_run_id == workflow_run_id).order_by(RoleRun.started_at)
            )
        )
        tools = list(
            self.session.exec(
                select(ToolRun).where(ToolRun.workflow_run_id == workflow_run_id).order_by(ToolRun.created_at)
            )
        )

        return {
            "workflow_run": run,
            "events": events,
            "role_runs": roles,
            "tool_runs": tools,
        }

    def _seed_mvp_workflow(self, task: Task, run: WorkflowRun) -> None:
        plan = {
            "goal": task.goal_text,
            "nodes": [
                {"id": "planner_start", "type": "TASK", "role": "Planner"},
                {"id": "operator_prepare", "type": "TOOL_CALL", "tool": "local_workspace"},
                {"id": "human_checkpoint", "type": "HUMAN_CHECKPOINT"},
                {"id": "reviewer_check", "type": "TASK", "role": "Reviewer"},
            ],
            "acceptance": [
                "workflow events are replayable",
                "high risk steps require checkpoint approval",
                "delivery includes evidence and confidence",
            ],
        }
        self._role_run(
            run.id,
            "Planner",
            {"task_id": task.id, "goal": task.goal_text},
            {"result": plan, "confidence": 0.72, "handoff": "operator_prepare"},
        )
        self._event(run.id, "PLAN_CREATED", {"plan": plan})

        self._tool_run(
            run.id,
            "local_workspace",
            {"permissions": ["fs.read"], "risk_level": "low"},
            {"task_id": task.id, "node_id": "operator_prepare"},
            {"workspace_ready": True},
        )
        self._role_run(
            run.id,
            "Operator",
            {"plan_node": "operator_prepare"},
            {"result": "workspace context prepared", "confidence": 0.8, "handoff": "human_checkpoint"},
        )
        self._event(run.id, "HUMAN_CHECKPOINT_REQUIRED", {"node_id": "human_checkpoint", "reason": "MVP governance gate"})

    def _role_run(self, run_id: int, role_name: str, input_payload: dict, output_payload: dict) -> None:
        now = datetime.utcnow()
        item = RoleRun(
            workflow_run_id=run_id,
            role_name=role_name,
            input_json=json.dumps(input_payload, ensure_ascii=False),
            output_json=json.dumps(output_payload, ensure_ascii=False),
            status="SUCCESS",
            started_at=now,
            ended_at=now,
        )
        self.session.add(item)
        self.session.commit()

    def _tool_run(
        self,
        run_id: int,
        tool_name: str,
        permission_snapshot: dict,
        input_payload: dict,
        output_payload: dict,
    ) -> None:
        item = ToolRun(
            workflow_run_id=run_id,
            tool_name=tool_name,
            permission_snapshot_json=json.dumps(permission_snapshot, ensure_ascii=False),
            input_json=json.dumps(input_payload, ensure_ascii=False),
            output_json=json.dumps(output_payload, ensure_ascii=False),
            duration_ms=1,
        )
        self.session.add(item)
        self.session.commit()

    def _event(self, run_id: int, event_type: str, payload: dict) -> None:
        event = WorkflowEvent(
            workflow_run_id=run_id,
            event_type=event_type,
            payload_json=json.dumps(payload, ensure_ascii=False),
            trace_id=f"wf-{run_id}-{int(datetime.utcnow().timestamp())}",
        )
        self.session.add(event)
        self.session.commit()

    def _audit(self, actor: str, action: str, target: str, decision: str, reason: str | None) -> None:
        audit = AuditLog(
            actor=actor,
            action=action,
            target=target,
            decision=decision,
            reason=reason,
            trace_id=f"audit-{actor}-{int(datetime.utcnow().timestamp())}",
        )
        self.session.add(audit)
        self.session.commit()
