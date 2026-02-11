import pytest
from app.core.settings import BackendSettings, InMemoryCheckpointerSettings, RedisCheckpointerSettings, get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    # Ensure each test gets a fresh settings instance
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _base_env(monkeypatch: pytest.MonkeyPatch, *, host_env: str | None = None, type_env: str | None = None):
    # Avoid loading the repository .env (contains extra keys) by clearing env_file for this test run.
    monkeypatch.setattr(
        BackendSettings,
        "model_config",
        {**BackendSettings.model_config, "env_file": None},
    )

    # Ensure a clean slate for checkpointer settings
    for var in [
        "RISKI_BACKEND__CHECKPOINTER__TYPE",
        "RISKI_BACKEND__CHECKPOINTER__HOST",
        "RISKI_BACKEND__CHECKPOINTER__PORT",
        "RISKI_BACKEND__CHECKPOINTER__DB",
        "RISKI_BACKEND__CHECKPOINTER__SECURE",
        "RISKI_BACKEND__CHECKPOINTER__PASSWORD",
        "RISKI_BACKEND__CHECKPOINTER__TTL_MINUTES",
    ]:
        monkeypatch.delenv(var, raising=False)

    if host_env is not None:
        monkeypatch.setenv("RISKI_BACKEND__CHECKPOINTER__HOST", host_env)

    if type_env is not None:
        monkeypatch.setenv("RISKI_BACKEND__CHECKPOINTER__TYPE", type_env)


@pytest.mark.usefixtures("clear_settings_cache")
def test_checkpointer_default_is_in_memory(monkeypatch: pytest.MonkeyPatch):
    """Default checkpointer settings should be in_memory when no env vars are present."""

    _base_env(monkeypatch, host_env=None)

    settings = get_settings()

    assert isinstance(settings.checkpointer, InMemoryCheckpointerSettings)
    assert settings.checkpointer.type == "in_memory"


@pytest.mark.usefixtures("clear_settings_cache")
def test_checkpointer_host_respects_env(monkeypatch: pytest.MonkeyPatch):
    """Env should override the checkpointer host value when type is set to redis."""

    _base_env(monkeypatch, host_env="my-redis", type_env="redis")

    settings = get_settings()

    assert isinstance(settings.checkpointer, RedisCheckpointerSettings)
    assert settings.checkpointer.host == "my-redis"
    assert settings.checkpointer.redis_url.encoded_string().startswith("redis://my-redis:6379/")
