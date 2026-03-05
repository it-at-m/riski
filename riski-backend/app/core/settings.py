from functools import lru_cache
from pathlib import Path
from typing import Literal, Union
from urllib.parse import quote

from pydantic import BaseModel, Field, RedisDsn, SecretStr, field_validator
from pydantic_settings import SettingsConfigDict

from core.settings.base import AppBaseSettings


class InMemoryCheckpointerSettings(BaseModel):
    type: Literal["in_memory"] = "in_memory"


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
        raw_password = self.password.get_secret_value() if self.password else None
        encoded_password = quote(raw_password, safe="") if raw_password else None
        return RedisDsn.build(
            scheme="rediss" if self.secure else "redis",
            username=None,
            password=encoded_password,
            host=self.host,
            port=self.port,
            path=f"/{self.db}",
        )


class BackendSettings(AppBaseSettings):
    """
    Application settings for the riski-backend.
    """

    version: str = Field(default="DUMMY FOR GITHUBACTION", description="The version of the riski backend.")
    frontend_version: str = Field(default="DUMMY FOR GITHUBACTION", description="The version of the riski frontend.")
    title: str = Field(default="RIS KI-Suche (Beta-Version)", description="The title of the application.")
    documentation_url: str = Field(default="https://ki.muenchen.de", description="The URL to the documentation.")

    @field_validator("version", "frontend_version", mode="before")
    @staticmethod
    def parse_version(value: str) -> str:
        """Parse version string to extract only the version number before @sha256."""
        if not isinstance(value, str):
            return value
        # Split by '@' and take the first part to remove the sha256 hash
        return value.split("@")[0]

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
    langfuse_system_prompt_name: str = Field(
        default="system",
        validation_alias="LANGFUSE_SYSTEM_PROMPT_NAME",
        description="Langfuse system prompt name",
    )
    langfuse_system_prompt_label: str = Field(
        default="production",
        validation_alias="LANGFUSE_SYSTEM_PROMPT_LABEL",
        description="Langfuse system prompt label",
    )
    langfuse_check_document_prompt_name: str = Field(
        default="check_document",
        validation_alias="LANGFUSE_CHECK_DOCUMENT_PROMPT_NAME",
        description="Langfuse check document prompt name",
    )
    langfuse_check_document_prompt_label: str = Field(
        default="production",
        validation_alias="LANGFUSE_CHECK_DOCUMENT_PROMPT_LABEL",
        description="Langfuse check document prompt label",
    )
    langfuse_agent_capabilities_prompt_name: str = Field(
        default="agent_capabilities",
        validation_alias="LANGFUSE_AGENT_CAPABILITIES_PROMPT_NAME",
        description="Langfuse prompt name for agent capabilities description",
    )
    langfuse_agent_capabilities_prompt_label: str = Field(
        default="production",
        validation_alias="LANGFUSE_AGENT_CAPABILITIES_PROMPT_LABEL",
        description="Langfuse prompt label for agent capabilities description",
    )

    # === Agent Settings ===
    checkpointer: Union[InMemoryCheckpointerSettings, RedisCheckpointerSettings] = Field(  # type: ignore
        discriminator="type",
        default={"type": "in_memory"},
        description="Settings for the agent's checkpointer.",
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

    top_k_docs: int = Field(
        default=10,
        ge=1,
        description="Number of documents to retrieve in corresponding tool",
    )

    db_query_timeout_seconds: int = Field(
        default=10,
        ge=1,
        description="Server-side statement timeout for database queries (seconds).",
    )

    db_query_total_timeout_seconds: int = Field(
        default=15,
        ge=1,
        description="Total asyncio timeout for database queries, including connection overhead (seconds).",
    )

    vectorstore_timeout_seconds: int = Field(
        default=15,
        ge=1,
        description="Total asyncio timeout for vector store similarity search (seconds).",
    )

    db_connect_timeout_seconds: int = Field(
        default=30,
        ge=1,
        description="Timeout for establishing a new database connection (seconds).",
    )

    check_document_max_concurrency: int = Field(
        default=1,
        ge=1,
        description="Maximum number of check_document fan-out branches that run concurrently. "
        "Lower values reduce parallel LLM API load at the cost of higher latency.",
        validation_alias="RISKI_BACKEND__CHECK_DOCUMENT_MAX_CONCURRENCY",
    )

    # === Debug / testing flags ===
    # Set via env var (e.g. RISKI_BACKEND__FORCE_VECTORSTORE_TIMEOUT=true) or config.yaml.
    # These immediately trigger the corresponding timeout path without needing a real
    # slow network call — useful for manual end-to-end testing.
    force_vectorstore_timeout: bool = Field(
        default=False,
        description="Force a vectorstore timeout on every retrieve_documents call (for testing).",
    )
    force_db_timeout: bool = Field(
        default=False,
        description="Force a database timeout on every retrieve_documents call (for testing).",
    )
    force_llm_timeout: bool = Field(
        default=False,
        description="Force an LLM timeout on every model call (for testing).",
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
    return BackendSettings()
