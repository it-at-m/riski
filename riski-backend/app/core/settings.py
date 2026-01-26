from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import SettingsConfigDict

from core.settings.base import AppBaseSettings


class BackendSettings(AppBaseSettings):
    """
    Application settings for the riski-backend.
    """

    version: str = Field(default="DUMMY FOR GITHUBACTION", description="The version of the riski backend.")
    enable_docs: bool = Field(default=False, description="Is the OpenAPI docs endpoint enabled.")

    # === Langfuse Settings ===
    langfuse_secret_key: SecretStr | None = Field(
        default=None,
        validation_alias="LANGFUSE_SECRET_KEY",
        description="Secret Key for Langfuse",
    )
    langfuse_public_key: SecretStr | None = Field(
        default=None,
        validation_alias="LANGFUSE_PUBLIC_KEY",
        description="Public Key for Langfuse",
    )
    langfuse_host: str | None = Field(
        default=None,
        validation_alias="LANGFUSE_HOST",
        description="Langfuse host",
    )

    # === Mock Langfuse Agent Settings ===
    mock_retrieval_delay_seconds: float = Field(
        default=0.4,
        validation_alias="MOCK_RETRIEVAL_DELAY_SECONDS",
    )
    mock_response_delay_seconds: float = Field(
        default=0.6,
        validation_alias="MOCK_RESPONSE_DELAY_SECONDS",
    )
    mock_retrieval_node: str = Field(
        default="RETRIEVAL",
        validation_alias="MOCK_RETRIEVAL_NODE",
    )
    mock_generate_node: str = Field(
        default="GENERATE",
        validation_alias="MOCK_GENERATE_NODE",
    )

    model_config = SettingsConfigDict(
        env_prefix="RISKI_BACKEND__",
        env_file=str(Path(__file__).resolve().parents[3] / ".env"),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
        cli_parse_args=False,
        cli_kebab_case=True,
        cli_prog_name="riski",
    )


@lru_cache(maxsize=1)
def get_settings() -> BackendSettings:
    """Get cached application settings."""
    return BackendSettings()  # type: ignore
