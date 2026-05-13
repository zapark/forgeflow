import json
from datetime import datetime
from typing import Any

from sqlmodel import Session

from app.models.audit import AuditLog
from app.models.workflow import ToolRun, WorkflowEvent, WorkflowRun
from app.schemas.tool import ToolSpec
from app.services.runtime_config_service import RuntimeConfigService


class ToolRuntimeService:
    def __init__(self, session: Session):
        self.session = session
        self.runtime_config = RuntimeConfigService(session)

    def execute(
        self,
        workflow_run_id: int,
        tool: ToolSpec,
        input_payload: dict[str, Any],
        actor: str = "system",
    ) -> dict | None:
        run = self.session.get(WorkflowRun, workflow_run_id)
        if run is None:
            return None

        missing_permissions = sorted(set(tool.permissions) - self.runtime_config.allowed_tool_permissions())
        if missing_permissions:
            reason = f"missing permissions: {','.join(missing_permissions)}"
            self._event(workflow_run_id, "TOOL_DENIED", {"tool_name": tool.tool_name, "reason": reason})
            self._audit(actor, "tool.execute", f"workflow_run:{workflow_run_id}", "DENY", reason)
            return {
                "status": "DENIED",
                "workflow_run_id": workflow_run_id,
                "event_type": "TOOL_DENIED",
                "reason": reason,
            }

        permission_snapshot = {
            "permissions": tool.permissions,
            "allowed_domains": tool.allowed_domains,
            "risk_level": tool.risk_level,
            "resource_limit": tool.resource_limit.model_dump(),
        }

        if tool.risk_level.lower() in self.runtime_config.checkpoint_tool_risk_levels():
            tool_run = self._tool_run(
                workflow_run_id,
                tool.tool_name,
                permission_snapshot,
                input_payload,
                None,
                {"checkpoint_required": True, "risk_level": tool.risk_level},
            )
            reason = f"risk level requires checkpoint: {tool.risk_level}"
            self._event(
                workflow_run_id,
                "TOOL_CHECKPOINT_REQUIRED",
                {"tool_name": tool.tool_name, "tool_run_id": tool_run.id, "reason": reason},
            )
            self._audit(actor, "tool.execute", f"workflow_run:{workflow_run_id}", "CHECKPOINT", reason)
            return {
                "status": "CHECKPOINT_REQUIRED",
                "tool_run_id": tool_run.id,
                "workflow_run_id": workflow_run_id,
                "event_type": "TOOL_CHECKPOINT_REQUIRED",
                "reason": reason,
            }

        output = self._safe_builtin_output(tool, input_payload)
        tool_run = self._tool_run(workflow_run_id, tool.tool_name, permission_snapshot, input_payload, output, None)
        self._event(
            workflow_run_id,
            "TOOL_EXECUTED",
            {"tool_name": tool.tool_name, "tool_run_id": tool_run.id, "output": output},
        )
        self._audit(actor, "tool.execute", f"workflow_run:{workflow_run_id}", "ALLOW", tool.tool_name)
        return {
            "status": "SUCCESS",
            "tool_run_id": tool_run.id,
            "workflow_run_id": workflow_run_id,
            "event_type": "TOOL_EXECUTED",
            "output": output,
        }

    def _safe_builtin_output(self, tool: ToolSpec, input_payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "tool_name": tool.tool_name,
            "version": tool.version,
            "accepted": True,
            "input_digest": len(json.dumps(input_payload, ensure_ascii=False, sort_keys=True)),
        }

    def _tool_run(
        self,
        workflow_run_id: int,
        tool_name: str,
        permission_snapshot: dict,
        input_payload: dict[str, Any],
        output_payload: dict[str, Any] | None,
        error_payload: dict[str, Any] | None,
    ) -> ToolRun:
        item = ToolRun(
            workflow_run_id=workflow_run_id,
            tool_name=tool_name,
            permission_snapshot_json=json.dumps(permission_snapshot, ensure_ascii=False),
            input_json=json.dumps(input_payload, ensure_ascii=False),
            output_json=json.dumps(output_payload, ensure_ascii=False) if output_payload is not None else None,
            error_json=json.dumps(error_payload, ensure_ascii=False) if error_payload is not None else None,
            duration_ms=1,
        )
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item

    def _event(self, workflow_run_id: int, event_type: str, payload: dict[str, Any]) -> None:
        event = WorkflowEvent(
            workflow_run_id=workflow_run_id,
            event_type=event_type,
            payload_json=json.dumps(payload, ensure_ascii=False),
            trace_id=f"wf-{workflow_run_id}-{int(datetime.utcnow().timestamp())}",
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
