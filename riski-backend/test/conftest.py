import pytest
from app.core.settings import BackendSettings, get_settings

# Apply immediately at import time so any module-level get_settings() calls during collection
# don't read the project .env or YAML config.
_ORIGINAL_MODEL_CONFIG = BackendSettings.model_config
BackendSettings.model_config = {
    **BackendSettings.model_config,
    "env_file": None,
    "yaml_file": None,
}
get_settings.cache_clear()


@pytest.fixture(scope="session", autouse=True)
def reset_settings_after_session():
    yield
    BackendSettings.model_config = _ORIGINAL_MODEL_CONFIG
    get_settings.cache_clear()
