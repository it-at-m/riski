from functools import lru_cache
from pathlib import Path

from core.settings.core import CoreSettings
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class OParlSettings(BaseSettings):
    """
    Settings for the standalone OParl publishing service.

    Database configuration is shared with the rest of the RISKI stack via the
    ``RISKI__DB__*`` environment variables (see ``core.settings.db``). All
    OParl-specific settings use the ``RISKI_OPARL__`` prefix.
    """

    # Shared core settings (db, genai, testdb). Read from the RISKI__* env tree,
    # identical to the other services.
    core: CoreSettings = Field(
        default_factory=lambda: CoreSettings(),
        validation_alias="RISKI",
    )

    # === Server ===
    server_host: str = Field(default="0.0.0.0", description="Host the OParl server binds to.")
    server_port: int = Field(default=8082, description="Port the OParl server binds to.")
    enable_docs: bool = Field(default=True, description="Expose the OpenAPI docs endpoints.")

    # === OParl ===
    base_url: str = Field(
        default="http://localhost:8082/oparl/v1",
        description="Public base URL under which this OParl API is reachable, "
        "including the version path. Object ids are derived from this. No trailing slash.",
    )
    oparl_version: str = Field(
        default="https://schema.oparl.org/1.1/",
        description="OParl version supported by this system.",
    )
    page_size: int = Field(default=50, ge=1, le=1000, description="Number of elements per page in external lists.")

    # === System / Body metadata (used as fallback if not present in the DB) ===
    system_name: str = Field(default="RISKI OParl Schnittstelle", description="Name of the OParl System object.")
    license: str | None = Field(
        default="https://www.govdata.de/dl-de/by-2-0",
        description="Default data license advertised by the System/Body.",
    )
    contact_email: str | None = Field(default=None, description="Contact email for the OParl API.")
    contact_name: str | None = Field(default=None, description="Contact name for the OParl API.")
    website: str | None = Field(default="https://risi.muenchen.de/risi", description="Website of the RIS.")
    vendor: str | None = Field(default="https://github.com/it-at-m/risKI", description="URL of the software vendor.")
    product: str | None = Field(default="https://github.com/it-at-m/risKI", description="URL of the used OParl server software.")

    body_name: str = Field(default="Landeshauptstadt München", description="Fallback Body name if none is stored in the DB.")
    body_short_name: str | None = Field(default="München", description="Fallback Body short name.")

    @field_validator("base_url", mode="after")
    @staticmethod
    def _strip_trailing_slash(value: str) -> str:
        return value.rstrip("/")

    model_config = SettingsConfigDict(
        env_prefix="RISKI_OPARL__",
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> OParlSettings:
    """Return the cached OParl settings instance."""
    return OParlSettings()
