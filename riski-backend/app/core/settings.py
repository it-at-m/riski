from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, RedisDsn, SecretStr
from pydantic_settings import SettingsConfigDict

from core.settings.base import AppBaseSettings


class InMemoryCheckpointerSettings(BaseModel):
    type: Literal["in_memory"] = "in_memory"


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
    checkpointer: InMemoryCheckpointerSettings | RedisCheckpointerSettings = Field(
        description="Settings for agent checkpointer",
        default_factory=InMemoryCheckpointerSettings,
        discriminator="type",
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

    # === Agent Settings ===
    checkpointer: "BaseCheckpointerSettings | None" = Field(
        description="Settings for agent checkpointer",
        default=None,
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


class RedisCheckpointerSettings(BaseModel):
    type: Literal["redis"] = "redis"
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
