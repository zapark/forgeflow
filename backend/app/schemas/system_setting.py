from pydantic import BaseModel


class SettingUpdate(BaseModel):
    value: str
    updated_by: str = "admin"
