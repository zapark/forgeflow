from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    actor: str
    action: str
    target: str
    decision: str
    reason: str | None = None
    trace_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
