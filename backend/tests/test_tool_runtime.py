from sqlmodel import SQLModel, Session, create_engine, select

from app.models.audit import AuditLog
from app.models.task import Task
from app.models.workflow import ToolRun, WorkflowEvent, WorkflowRun
from app.schemas.tool import ToolSpec
from app.services.tool_runtime_service import ToolRuntimeService


def make_session():
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def make_run(session: Session) -> WorkflowRun:
    task = Task(title="tool task", goal_text="test tool runtime")
    session.add(task)
    session.commit()
    session.refresh(task)

    run = WorkflowRun(task_id=task.id)
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def test_low_risk_allowed_tool_executes_and_records_trace():
    with make_session() as session:
        run = make_run(session)
        result = ToolRuntimeService(session).execute(
            run.id,
            ToolSpec(tool_name="local_context", permissions=["fs.read"], risk_level="low"),
            {"path": "."},
            actor="operator",
        )

        assert result["status"] == "SUCCESS"
        assert result["event_type"] == "TOOL_EXECUTED"

        tool_runs = list(session.exec(select(ToolRun).where(ToolRun.workflow_run_id == run.id)))
        assert len(tool_runs) == 1
        assert tool_runs[0].output_json is not None
        assert tool_runs[0].error_json is None

        events = list(session.exec(select(WorkflowEvent).where(WorkflowEvent.workflow_run_id == run.id)))
        assert [e.event_type for e in events] == ["TOOL_EXECUTED"]

        audits = list(session.exec(select(AuditLog).where(AuditLog.action == "tool.execute")))
        assert audits[0].decision == "ALLOW"


def test_tool_runtime_denies_missing_permission_without_tool_run():
    with make_session() as session:
        run = make_run(session)
        result = ToolRuntimeService(session).execute(
            run.id,
            ToolSpec(tool_name="shell", permissions=["shell.exec"], risk_level="high"),
            {"command": "echo hi"},
            actor="operator",
        )

        assert result["status"] == "DENIED"
        assert result["event_type"] == "TOOL_DENIED"

        tool_runs = list(session.exec(select(ToolRun).where(ToolRun.workflow_run_id == run.id)))
        assert tool_runs == []

        audits = list(session.exec(select(AuditLog).where(AuditLog.action == "tool.execute")))
        assert audits[0].decision == "DENY"


def test_high_risk_allowed_tool_requires_checkpoint():
    with make_session() as session:
        run = make_run(session)
        result = ToolRuntimeService(session).execute(
            run.id,
            ToolSpec(tool_name="sensitive_write", permissions=["fs.read"], risk_level="high"),
            {"target": "sensitive"},
            actor="operator",
        )

        assert result["status"] == "CHECKPOINT_REQUIRED"
        assert result["event_type"] == "TOOL_CHECKPOINT_REQUIRED"

        tool_runs = list(session.exec(select(ToolRun).where(ToolRun.workflow_run_id == run.id)))
        assert len(tool_runs) == 1
        assert tool_runs[0].output_json is None
        assert tool_runs[0].error_json is not None

        audits = list(session.exec(select(AuditLog).where(AuditLog.action == "tool.execute")))
        assert audits[0].decision == "CHECKPOINT"
