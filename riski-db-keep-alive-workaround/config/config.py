from functools import lru_cache
from logging import Logger
from os import getenv

from pydantic import AliasChoices, Field
from pydantic_settings import (
    BaseSettings,
    CliSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from src.logtools import getLogger

logger: Logger


class Config(BaseSettings):
    """
    Project-wide configuration class.

    Supports loading from:
    - Command line arguments
    - Environment variables (.env)
    - YAML config files (e.g., config.yaml)
    """

    # === Scraper / Extractor Settings ===
    request_url: str = Field(
        default="http://google.de",
        validation_alias=AliasChoices("REQUEST_URL", "request_url"),
        description="Target URL for requests",
    )
    request_interval: int = Field(
        default=10,
        validation_alias=AliasChoices("REQUEST_INTERVAL", "request_interval"),
        description="Interval for requests",
    )

    # === Settings Behavior ===
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
        yaml_file=getenv("RISKI__CONFIG", "config.yaml"),
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

    def print_config(self):
        logger = getLogger()
        logger.info(self.model_dump())


@lru_cache
def get_config() -> Config:
    """Returns the cached project config instance."""
    return Config()
