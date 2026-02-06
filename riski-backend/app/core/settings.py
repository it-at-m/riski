from abc import ABC
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, RedisDsn, SecretStr, model_validator
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

    # === Agent Settings ===
    checkpointer: "RedisCheckpointerSettings | None" = Field(
        description="Settings for agent checkpointer",
        default=None,
    )

    # === Server Settings ===
    server_host: str = Field(
        default="localhost",
        description="The host for the riski-backend server to bind to.",
    )
    server_port: int = Field(
        default=8080,
        description="The port for the riski-backend server to bind to.",
    )

    @model_validator(mode="before")
    @classmethod
    def check_checkpointer_env(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # If checkpointer is implicitly initialized via env vars (nested dict),
            # but currently remains None because Pydantic V2 optional behavior might prefer None default,
            # we check os.environ for relevant keys to force initialization.
            if "checkpointer" not in data or data.get("checkpointer") is None:
                import os

                # Check for any env var starting with RISKI_BACKEND__CHECKPOINTER__
                # (Ignoring case as Windows env is case-insensitive, but Linux is sensitive.
                # Pydantic Settings is configured with cli_kebab_case=True but env_prefix usually upper).
                prefix = "RISKI_BACKEND__CHECKPOINTER__"
                has_env = any(k.upper().startswith(prefix) for k in os.environ.keys())

                if has_env:
                    # Pydantic V2 Settings does not automatically instantiate nested models from environment variables
                    # if the field defaults to None. We manually check for the environment variable prefix and
                    # build the dictionary to force instantiation.
                    checkpointer_data = {}
                    for field in ["host", "port", "db", "secure", "password", "ttl_minutes"]:
                        env_key = f"{prefix}{field.upper()}"
                        val = os.getenv(env_key)
                        if val is not None:
                            checkpointer_data[field] = val

                    if checkpointer_data:
                        data["checkpointer"] = checkpointer_data

        return data

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


class BaseCheckpointerSettings(BaseModel, ABC):
    """Base settings for agent checkpointers."""

    pass


class RedisCheckpointerSettings(BaseCheckpointerSettings):
    host: str = Field(
        default="localhost",
        description="Redis host for checkpointer",
    )
    port: int = Field(
        default=6379,
        description="Redis port for checkpointer",
    )
    db: int = Field(
        default=0,
        description="Redis database number for checkpointer",
    )
    password: SecretStr | None = Field(
        default=None,
        description="Redis password for checkpointer",
    )
    secure: bool = Field(
        default=False,
        description="Use SSL/TLS for Redis connection",
    )
    ttl_minutes: int = Field(
        default=720,
        description="TTL for checkpoints in minutes",
    )

    @property
    def redis_url(self) -> RedisDsn:
        """Construct the Redis DSN URL."""
        return RedisDsn.build(
            scheme="rediss" if self.secure else "redis",
            username=None,
            password=self.password.get_secret_value() if self.password else None,
            host=self.host,
            port=self.port,
            path=f"/{self.db}",
        )


@lru_cache(maxsize=1)
def get_settings() -> BackendSettings:
    """Get cached application settings."""
    return BackendSettings()
