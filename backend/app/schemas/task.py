from pydantic import BaseModel


class TaskCreate(BaseModel):
    title: str
    goal: str


class TaskControl(BaseModel):
    action: str
    reason: str | None = None
    actor: str = "user"
