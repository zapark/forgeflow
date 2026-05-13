from sqlmodel import SQLModel, Session, create_engine

from app.models.system_setting import SystemSetting
from app.services.runtime_config_service import RuntimeConfigService


def make_session():
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_runtime_config_prefers_db_value_over_env_default():
    with make_session() as session:
        session.add(SystemSetting(key="ALLOWED_TASK_ACTIONS", value="pause", updated_by="tester"))
        session.commit()

        svc = RuntimeConfigService(session)
        actions = svc.allowed_actions()
        assert actions == {"pause"}


def test_runtime_config_falls_back_to_env_default_when_db_missing():
    with make_session() as session:
        svc = RuntimeConfigService(session)
        default_limit = svc.timeline_default_limit()
        max_limit = svc.timeline_max_limit()

        assert isinstance(default_limit, int)
        assert isinstance(max_limit, int)
        assert default_limit > 0
        assert max_limit >= default_limit
