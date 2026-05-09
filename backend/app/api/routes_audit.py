from datetime import datetime
import csv
import io

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sqlmodel import select

from app.core.db import get_session
from app.models.audit import AuditLog

router = APIRouter(tags=["audit"])


@router.get("/audit")
def list_audit(
    actor: str | None = None,
    action: str | None = None,
    decision: str | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
):
    with get_session() as session:
        query = select(AuditLog)
        if actor:
            query = query.where(AuditLog.actor == actor)
        if action:
            query = query.where(AuditLog.action == action)
        if decision:
            query = query.where(AuditLog.decision == decision)
        if start_at:
            query = query.where(AuditLog.created_at >= start_at)
        if end_at:
            query = query.where(AuditLog.created_at <= end_at)
        query = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
        return list(session.exec(query))


@router.get("/audit/task/{task_id}")
def list_task_audit(task_id: int, limit: int = 100, offset: int = 0):
    with get_session() as session:
        query = (
            select(AuditLog)
            .where(AuditLog.target == f"task:{task_id}")
            .order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(session.exec(query))


@router.get("/audit/export.csv")
def export_audit_csv(
    actor: str | None = None,
    action: str | None = None,
    decision: str | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    limit: int = 1000,
):
    with get_session() as session:
        query = select(AuditLog)
        if actor:
            query = query.where(AuditLog.actor == actor)
        if action:
            query = query.where(AuditLog.action == action)
        if decision:
            query = query.where(AuditLog.decision == decision)
        if start_at:
            query = query.where(AuditLog.created_at >= start_at)
        if end_at:
            query = query.where(AuditLog.created_at <= end_at)
        query = query.order_by(AuditLog.created_at.desc()).limit(limit)
        rows = list(session.exec(query))

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "actor", "action", "target", "decision", "reason", "trace_id", "created_at"])
    for r in rows:
        writer.writerow([r.id, r.actor, r.action, r.target, r.decision, r.reason or "", r.trace_id, r.created_at.isoformat()])

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_export.csv"},
    )


@router.get("/audit/stats")
def audit_stats(start_at: datetime | None = None, end_at: datetime | None = None):
    with get_session() as session:
        query = select(AuditLog)
        if start_at:
            query = query.where(AuditLog.created_at >= start_at)
        if end_at:
            query = query.where(AuditLog.created_at <= end_at)
        rows = list(session.exec(query))

    by_action: dict[str, int] = {}
    by_decision: dict[str, int] = {}
    for r in rows:
        by_action[r.action] = by_action.get(r.action, 0) + 1
        by_decision[r.decision] = by_decision.get(r.decision, 0) + 1

    return {
        "total": len(rows),
        "by_action": by_action,
        "by_decision": by_decision,
    }
