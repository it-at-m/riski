import pytest
from app.core.settings import BackendSettings, get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    # Ensure each test gets a fresh settings instance
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _base_env(monkeypatch: pytest.MonkeyPatch, *, host_env: str | None = None):
    # Avoid loading the repository .env (contains extra keys) by clearing env_file for this test run.
    monkeypatch.setattr(
        BackendSettings,
        "model_config",
        {**BackendSettings.model_config, "env_file": None},
    )
    if host_env is None:
        monkeypatch.delenv("RISKI_BACKEND__CHECKPOINTER__HOST", raising=False)
    else:
        monkeypatch.setenv("RISKI_BACKEND__CHECKPOINTER__HOST", host_env)


@pytest.mark.usefixtures("clear_settings_cache")
def test_checkpointer_default_host_is_redis(monkeypatch: pytest.MonkeyPatch):
    """Default checkpointer host should be the Redis service name."""

    _base_env(monkeypatch, host_env=None)

    settings = get_settings()

    assert settings.checkpointer.host == "redis"
    assert settings.checkpointer.redis_url.encoded_string().startswith("redis://redis:6379/")


@pytest.mark.usefixtures("clear_settings_cache")
def test_checkpointer_host_respects_env(monkeypatch: pytest.MonkeyPatch):
    """Env should override the checkpointer host value."""

    _base_env(monkeypatch, host_env="my-redis")

    settings = get_settings()

    assert settings.checkpointer.host == "my-redis"
    assert settings.checkpointer.redis_url.encoded_string().startswith("redis://my-redis:6379/")
