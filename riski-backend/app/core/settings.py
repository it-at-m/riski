from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict, YamlConfigSettingsSource


class Settings(BaseSettings):
    """
    Application settings for the  riski-backend.
    """

    version: str = Field(description="The version of the riski backend.")
    enable_docs: bool = Field(default=False, description="Is the OpenAPI docs endpoint enabled.")

    model_config = SettingsConfigDict(
        env_prefix="RISKI_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
        yaml_file="config.yaml",
        yaml_file_encoding="utf-8",
        cli_parse_args=False,
        cli_kebab_case=True,
        cli_prog_name="riski",
    )

    # Reorder settings sources to prioritize YAML config
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],  # type: ignore
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            YamlConfigSettingsSource(settings_cls),
            dotenv_settings,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: The application settings.
    """
    return Settings()  # type: ignore
