from sqlmodel import SQLModel, Session, create_engine, select

from app.models.audit import AuditLog
from app.models.task import Task, TaskStatus
from app.models.workflow import RoleRun, ToolRun, WorkflowEvent, WorkflowStatus
from app.services.execution_service import ExecutionService


def make_session():
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_start_execution_seeds_mvp_replayable_workflow():
    with make_session() as session:
        task = Task(title="daily report", goal_text="prepare daily industry report")
        session.add(task)
        session.commit()
        session.refresh(task)

        svc = ExecutionService(session)
        run = svc.start_execution(task.id)

        assert run is not None
        assert run.status == WorkflowStatus.WAITING_HUMAN
        assert run.current_node_id == "human_checkpoint"

        refreshed_task = session.get(Task, task.id)
        assert refreshed_task.status == TaskStatus.WAITING_HUMAN

        events = list(session.exec(select(WorkflowEvent).where(WorkflowEvent.workflow_run_id == run.id)))
        assert [e.event_type for e in events] == [
            "EXECUTION_STARTED",
            "PLAN_CREATED",
            "HUMAN_CHECKPOINT_REQUIRED",
        ]

        roles = list(session.exec(select(RoleRun).where(RoleRun.workflow_run_id == run.id)))
        assert [r.role_name for r in roles] == ["Planner", "Operator"]

        tools = list(session.exec(select(ToolRun).where(ToolRun.workflow_run_id == run.id)))
        assert len(tools) == 1
        assert tools[0].tool_name == "local_workspace"

        audits = list(session.exec(select(AuditLog).where(AuditLog.action == "execution.start")))
        assert len(audits) == 1
        assert audits[0].decision == "ALLOW"


def test_replay_returns_events_roles_and_tools():
    with make_session() as session:
        task = Task(title="weekly", goal_text="write a weekly summary")
        session.add(task)
        session.commit()
        session.refresh(task)

        svc = ExecutionService(session)
        run = svc.start_execution(task.id)

        replay = svc.replay(run.id)

        assert replay is not None
        assert replay["workflow_run"].id == run.id
        assert len(replay["events"]) == 3
        assert len(replay["role_runs"]) == 2
        assert len(replay["tool_runs"]) == 1
