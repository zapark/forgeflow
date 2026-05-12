from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class SystemSetting(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)
    value: str
    updated_by: str = Field(default="system")
    updated_at: datetime = Field(default_factory=datetime.utcnow)
