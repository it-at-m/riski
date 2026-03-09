import pytest
from app.core.settings import BackendSettings, get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _base_env(monkeypatch: pytest.MonkeyPatch):
    # Avoid loading the repository .env (contains extra keys) by clearing env_file for this test run.
    monkeypatch.setattr(
        BackendSettings,
        "model_config",
        {**BackendSettings.model_config, "env_file": None, "yaml_file": None},
    )

    # Ensure a clean slate for optional settings
    for var in [
        "RISKI_BACKEND__SERVER_HOST",
        "RISKI_BACKEND__SERVER_PORT",
        "RISKI_BACKEND__ENABLE_DOCS",
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "LANGFUSE_HOST",
        "RISKI_BACKEND__CHECKPOINTER__TYPE",
        "RISKI_BACKEND__CHECKPOINTER__HOST",
        "RISKI_BACKEND__CHECKPOINTER__SECURE",
        "RISKI_BACKEND__CHECKPOINTER__PORT",
        "RISKI_BACKEND__CHECKPOINTER__DB",
        "RISKI_BACKEND__CHECKPOINTER__TTL_MINUTES",
        "RISKI_BACKEND__CHECKPOINTER__PASSWORD",
    ]:
        monkeypatch.delenv(var, raising=False)


def test_server_defaults(monkeypatch: pytest.MonkeyPatch):
    """Server-related settings should fall back to defaults when not provided."""

    _base_env(monkeypatch)

    settings = get_settings()

    assert settings.server_host == "localhost"
    assert settings.server_port == 8080
    assert settings.enable_docs is False


def test_server_and_langfuse_overrides(monkeypatch: pytest.MonkeyPatch):
    """Env vars should override server and Langfuse settings."""

    _base_env(monkeypatch)
    monkeypatch.setenv("RISKI_BACKEND__SERVER_HOST", "0.0.0.0")
    monkeypatch.setenv("RISKI_BACKEND__SERVER_PORT", "9090")
    monkeypatch.setenv("RISKI_BACKEND__ENABLE_DOCS", "true")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pub-key")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sec-key")
    monkeypatch.setenv("LANGFUSE_HOST", "https://langfuse.local")

    settings = get_settings()

    assert settings.server_host == "0.0.0.0"
    assert settings.server_port == 9090
    assert settings.enable_docs is True
    assert settings.langfuse_public_key.get_secret_value() == "pub-key"
    assert settings.langfuse_secret_key.get_secret_value() == "sec-key"
    assert settings.langfuse_host == "https://langfuse.local"


def test_checkpointer_secure_overrides(monkeypatch: pytest.MonkeyPatch):
    """Secure Redis settings should be applied and reflected in the DSN."""

    _base_env(monkeypatch)
    monkeypatch.setenv("RISKI_BACKEND__CHECKPOINTER__TYPE", "redis")
    monkeypatch.setenv("RISKI_BACKEND__CHECKPOINTER__SECURE", "true")
    monkeypatch.setenv("RISKI_BACKEND__CHECKPOINTER__PORT", "6380")
    monkeypatch.setenv("RISKI_BACKEND__CHECKPOINTER__DB", "5")
    monkeypatch.setenv("RISKI_BACKEND__CHECKPOINTER__TTL_MINUTES", "123")
    monkeypatch.setenv("RISKI_BACKEND__CHECKPOINTER__PASSWORD", "s3cr3t")

    settings = get_settings()
    cp = settings.checkpointer

    assert cp.secure is True
    assert cp.port == 6380
    assert cp.db == 5
    assert cp.ttl_minutes == 123
    assert cp.password.get_secret_value() == "s3cr3t"

    url = cp.redis_url.encoded_string()
    assert url.startswith("rediss://")
    assert cp.redis_url.host == "localhost"
    assert cp.redis_url.port == 6380
    assert cp.redis_url.path.strip("/") == "5"
