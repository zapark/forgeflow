from datetime import datetime

from fastapi import APIRouter
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
