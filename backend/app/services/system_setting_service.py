from datetime import datetime

from sqlmodel import Session, select

from app.models.system_setting import SystemSetting


class SystemSettingService:
    def __init__(self, session: Session):
        self.session = session

    def list_settings(self) -> list[SystemSetting]:
        return list(self.session.exec(select(SystemSetting).order_by(SystemSetting.key)))

    def get_setting(self, key: str) -> SystemSetting | None:
        return self.session.exec(select(SystemSetting).where(SystemSetting.key == key)).first()

    def upsert_setting(self, key: str, value: str, updated_by: str) -> SystemSetting:
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
        return setting
