from functools import lru_cache
from pathlib import Path

from core.settings.base import AppBaseSettings
from pydantic_settings import SettingsConfigDict


class DocPipelineSettings(AppBaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_prefix="RISKI__DOCUMENTS__",  # only applies to doc-pipeline-related fields
    )


@lru_cache
def get_settings() -> DocPipelineSettings:
    """Returns the cached project config instance."""
    return DocPipelineSettings()
