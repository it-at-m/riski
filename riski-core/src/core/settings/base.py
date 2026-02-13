from os import getenv

from core.settings.core import CoreSettings
from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import (
    BaseSettings,
    CliSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)
from truststore import inject_into_ssl


class AppBaseSettings(BaseSettings):
    core: CoreSettings = Field(
        default_factory=lambda: CoreSettings(),
        validation_alias="RISKI",
    )
    # === General Settings ===
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
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

    # === OpenAI Settings ===
    openai_api_key: SecretStr = Field(
        ...,
        validation_alias=AliasChoices("OPENAI_API_KEY"),
        description="API key for OpenAI",
    )
    openai_api_base: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_API_BASE"),
        description="Base URL for OpenAI API",
    )
    openai_api_version: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_API_VERSION"),
        description="Version of the OpenAI API to use",
    )
    tiktoken_cache_dir: str = Field(
        default="tiktoken_cache",
        validation_alias=AliasChoices("TIKTOKEN_CACHE_DIR"),
        description="Directory to store tiktoken cache",
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

    def __init__(self, **kwargs):
        # Inject SSL before anything else happens
        inject_into_ssl()
        super().__init__(**kwargs)
