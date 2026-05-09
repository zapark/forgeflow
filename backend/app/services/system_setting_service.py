from datetime import datetime

from sqlmodel import Session, select

from app.core.config import settings
from app.models.audit import AuditLog
from app.models.system_setting import SystemSetting


class SystemSettingService:
    def __init__(self, session: Session):
        self.session = session

    def list_settings(self) -> list[SystemSetting]:
        return list(self.session.exec(select(SystemSetting).order_by(SystemSetting.key)))

    def get_setting(self, key: str) -> SystemSetting | None:
        return self.session.exec(select(SystemSetting).where(SystemSetting.key == key)).first()

    def upsert_setting(self, key: str, value: str, updated_by: str) -> SystemSetting:
        if key not in settings.editable_setting_keys_set:
            raise ValueError(f"setting key not editable: {key}")
        setting = self.get_setting(key)
        if setting is None:
            setting = SystemSetting(key=key, value=value, updated_by=updated_by)
        else:
            setting.value = value
            setting.updated_by = updated_by
            setting.updated_at = datetime.utcnow()
        self.session.add(setting)
        self.session.commit()
        self.session.refresh(setting)

        audit = AuditLog(
            actor=updated_by,
            action="setting.upsert",
            target=f"setting:{key}",
            decision="ALLOW",
            reason=f"value={value}",
            trace_id=f"setting-{key}",
        )
        self.session.add(audit)
        self.session.commit()
        return setting
