from fastapi import APIRouter, HTTPException

from app.core.db import get_session
from app.schemas.system_setting import SettingUpdate
from app.services.system_setting_service import SystemSettingService

router = APIRouter(tags=["settings"])


@router.get("/settings")
def list_settings():
    with get_session() as session:
        return SystemSettingService(session).list_settings()


@router.get("/settings/{key}")
def get_setting(key: str):
    with get_session() as session:
        setting = SystemSettingService(session).get_setting(key)
    if setting is None:
        raise HTTPException(status_code=404, detail="setting not found")
    return setting


@router.put("/settings/{key}")
def upsert_setting(key: str, payload: SettingUpdate):
    with get_session() as session:
        setting = SystemSettingService(session).upsert_setting(key=key, value=payload.value, updated_by=payload.updated_by)
    return setting
