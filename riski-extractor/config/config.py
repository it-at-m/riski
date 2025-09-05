import datetime
from functools import lru_cache
from logging import Logger
from os import getenv
from pathlib import Path

from pydantic import AliasChoices, Field, HttpUrl, PostgresDsn
from pydantic_settings import (
    BaseSettings,
    CliSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)
from src.logtools import getLogger
from truststore import inject_into_ssl

logger: Logger


class Config(BaseSettings):
    """
    Project-wide configuration class.

    Supports loading from:
    - Command line arguments
    - Environment variables (.env)
    - YAML config files (e.g., config.yaml)
    """

    # === General Settings ===
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )

    # === Scraper / Extractor Settings ===
    base_url: HttpUrl = Field(
        default="https://risi.muenchen.de/risi",
        description="Main target URL or domain to scrape",
    )
    allowed_domains: list[str] = Field(
        default_factory=list,
        description="Domains that the scraper is allowed to follow",
    )
    start_paths: list[str] = Field(
        default_factory=list,
        description="Initial paths to begin scraping from (relative to base_url)",
    )
    start_date: str = Field(
        default=datetime.date.today().isoformat(),
        description="Start date for scraping (ISO format YYYY-MM-DD)",
    )
    end_date: str = Field(
        default=datetime.date.today().isoformat(),
        description="Start date for scraping (ISO format YYYY-MM-DD)",
    )

    user_agent: str = Field(
        default="Mozilla/5.0 (compatible; ScraperBot/1.0)",
        description="User-Agent header for requests",
    )

    http_proxy: str | None = Field(
        default=None,
        validation_alias=AliasChoices("HTTP_PROXY", "http_proxy"),
        description="HTTP proxy to use for requests",
    )
    https_proxy: str | None = Field(
        default=None,
        validation_alias=AliasChoices("HTTPS_PROXY", "https_proxy"),
        description="HTTPS proxy to use for requests",
    )
    no_proxy: str | None = Field(
        default=None,
        validation_alias=AliasChoices("NO_PROXY", "no_proxy"),
        description="Comma-separated list of hosts to bypass the proxy",
    )

    request_timeout: int = Field(
        default=10,
        ge=1,
        description="Request timeout in seconds",
    )

    max_retries: int = Field(
        default=5,
        ge=0,
        description="Number of retries on failed requests",
    )

    # === OpenAI Settings ===
    openai_api_key: str = Field(
        ...,
        validation_alias="OPENAI_API_KEY",
        description="API key for OpenAI",
    )
    openai_api_base: str | None = Field(
        default=None,
        validation_alias="OPENAI_API_BASE",
        description="Base URL for OpenAI API",
    )
    openai_api_version: str | None = Field(
        default=None,
        validation_alias="OPENAI_API_VERSION",
        description="Version of the OpenAI API to use",
    )
    tiktoken_cache_dir: str = Field(
        default="tiktoken_cache",
        validation_alias="TIKTOKEN_CACHE_DIR",
        description="Directory to store tiktoken cache",
    )
    riski_openai_embedding_model: str = Field(
        default="text-embedding-3-large",
        validation_alias="RISKI_OPENAI_EMBEDDING_MODEL",
        description="OpenAI embedding model to use",
    )

    # === Postgres Settings ===
    riski_db_name: str = Field(
        validation_alias="RISKI_DB_NAME",
        description="Postgres database name",
    )
    riski_db_user: str = Field(
        validation_alias="RISKI_DB_USER",
        description="Postgres username",
    )
    riski_db_password: str = Field(
        validation_alias="RISKI_DB_PASSWORD",
        description="Postgres password",
    )
    database_url: PostgresDsn | None = Field(
        default=None,
        validation_alias="DATABASE_URL",
        description="Full Postgres connection URL",
    )

    # === Test Database (Optional) ===
    test_riski_db_name: str | None = Field(
        default=None,
        validation_alias="TEST_RISKI_DB_NAME",
        description="Test database name",
    )
    test_riski_db_user: str | None = Field(
        default=None,
        validation_alias="TEST_RISKI_DB_USER",
        description="Test database username",
    )
    test_riski_db_password: str | None = Field(
        default=None,
        validation_alias="TEST_RISKI_DB_PASSWORD",
        description="Test database password",
    )
    test_database_url: PostgresDsn | None = Field(
        default=None,
        validation_alias="TEST_DATABASE_URL",
        description="Full test database connection URL",
    )

    # === Settings Behavior ===
    model_config = SettingsConfigDict(
        env_prefix="RISKI_EXTRAKTOR_",  # only applies to extractor-related fields
        env_file=str((Path(__file__).resolve().parents[2] / ".env")),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
        yaml_file=getenv("RISKI_EXTRAKTOR_CONFIG", "config.yaml"),
        yaml_file_encoding="utf-8",
        cli_parse_args=True,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            CliSettingsSource(settings_cls),
            env_settings,
            YamlConfigSettingsSource(settings_cls),
            dotenv_settings,
        )

    def __init__(self, **kwargs):
        # Inject SSL before anything else happens
        inject_into_ssl()
        super().__init__(**kwargs)

    def print_config(self):
        logger = getLogger()
        logger.debug(
            self.model_dump(
                exclude={
                    "openai_api_key",
                    "riski_db_password",
                    "database_url",
                    "test_riski_db_password",
                    "test_database_url",
                }
            )
        )


@lru_cache
def get_config() -> Config:
    """Returns the cached project config instance."""
    return Config()
