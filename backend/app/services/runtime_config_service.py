from sqlmodel import Session

from app.core.config import settings
from app.services.system_setting_service import SystemSettingService


class RuntimeConfigService:
    def __init__(self, session: Session):
        self.session = session
        self.setting_service = SystemSettingService(session)

    def get(self, key: str, default: str) -> str:
        item = self.setting_service.get_setting(key)
        if item is None:
            return default
        return item.value

    def allowed_actions(self) -> set[str]:
        raw = self.get("ALLOWED_TASK_ACTIONS", settings.allowed_task_actions)
        return {x.strip() for x in raw.split(",") if x.strip()}

    def timeline_default_limit(self) -> int:
        raw = self.get("TIMELINE_DEFAULT_LIMIT", str(settings.timeline_default_limit))
        return int(raw)

    def timeline_max_limit(self) -> int:
        raw = self.get("TIMELINE_MAX_LIMIT", str(settings.timeline_max_limit))
        return int(raw)
