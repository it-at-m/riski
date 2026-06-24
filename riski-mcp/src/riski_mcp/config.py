"""Configuration for the RISKI MCP server (issue #05).

All settings use the ``RISKI_MCP__`` prefix and can be supplied via environment
variables or a local ``.env`` file. On Hugging Face, secrets and variables are
injected as environment variables at runtime, so no extra SDK is needed.
"""

from functools import lru_cache

from pydantic import Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the RISKI MCP server.

    Values are read from environment variables prefixed with ``RISKI_MCP__``
    (e.g. ``RISKI_MCP__BACKEND_URL``) or from a ``.env`` file in the working
    directory. ``BACKEND_URL`` is required; everything else has a sane default.
    """

    model_config = SettingsConfigDict(
        env_prefix="RISKI_MCP__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    backend_url: HttpUrl = Field(
        ...,
        description="Base URL of the deployed RISKI backend (required).",
    )
    backend_auth_header: str | None = Field(
        default=None,
        description="Optional Authorization/API-key header value sent to the backend.",
    )
    request_timeout_seconds: float = Field(
        default=60.0,
        gt=0,
        description="Overall timeout for a single agent run / AG-UI stream.",
    )
    connect_timeout_seconds: float = Field(
        default=10.0,
        gt=0,
        description="httpx connect timeout.",
    )
    max_sources: int = Field(
        default=3,
        ge=0,
        description="Maximum number of sources appended to a spoken answer.",
    )
    verify_ssl: bool = Field(
        default=True,
        description="Verify TLS certificates. Prefer truststore for corporate CAs.",
    )
    log_level: str = Field(
        default="INFO",
        description="Log level for the MCP server.",
    )

    @field_validator("log_level")
    @classmethod
    def _normalize_log_level(cls, value: str) -> str:
        return value.upper()

    @property
    def backend_base_url(self) -> str:
        """Backend base URL as a plain string without a trailing slash."""
        return str(self.backend_url).rstrip("/")


@lru_cache
def get_settings() -> Settings:
    """Return the cached :class:`Settings`, loaded once per process.

    Raises:
        pydantic.ValidationError: if ``RISKI_MCP__BACKEND_URL`` is missing or any
            value is invalid. Surfaced at startup so the Space fails fast with a
            clear message instead of returning a 500 mid-request.
    """
    return Settings()  # type: ignore[call-arg]  # values come from env / .env
