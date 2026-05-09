from fastapi import APIRouter, HTTPException

from app.core.db import get_session, init_db
from app.schemas.task import TaskControl, TaskCreate
from app.services.task_service import TaskService

router = APIRouter(tags=["tasks"])
init_db()


@router.post("/tasks")
def create_task(payload: TaskCreate):
    with get_session() as session:
        task = TaskService(session).create_task(payload)
    return {"task_id": task.id, "status": task.status}


@router.get("/tasks")
def list_tasks():
    with get_session() as session:
        tasks = TaskService(session).list_tasks()
    return tasks


@router.get("/tasks/{task_id}")
def get_task(task_id: int):
    with get_session() as session:
        task = TaskService(session).get_task(task_id)
    if task is None:
        raise HTTPException(status_code=400, detail="task not found or invalid action")
    return task


@router.post("/tasks/{task_id}/control")
def control_task(task_id: int, payload: TaskControl):
    with get_session() as session:
        task = TaskService(session).control_task(task_id, payload.action, payload.actor, payload.reason)
    if task is None:
        raise HTTPException(status_code=400, detail="task not found or invalid action")
    return {"task_id": task.id, "status": task.status}
