import datetime
from functools import lru_cache
from logging import Logger
from pathlib import Path

from core.settings.base import AppBaseSettings
from pydantic import Field, HttpUrl, model_validator
from pydantic_settings import SettingsConfigDict

from src.logtools import getLogger

logger: Logger


class Config(AppBaseSettings):
    """
    Project-wide configuration class.

    Supports loading from:
    - Command line arguments
    - Environment variables (.env)
    - YAML config files (e.g., config.yaml)
    """

    # === Scraper / Extractor Settings ===
    base_url: HttpUrl = Field(
        default=HttpUrl("https://risi.muenchen.de/risi"),
        description="Main target URL or domain to scrape",
    )
    start_date: str = Field(
        default=datetime.date.today().isoformat(),
        description="Start date for scraping (ISO format YYYY-MM-DD)",
    )
    end_date: str | None = Field(
        default=None,
        description="End date for scraping (ISO format YYYY-MM-DD)",
    )
    user_agent: str = Field(
        default="Mozilla/5.0 (compatible; ScraperBot/1.0)",
        description="User-Agent header for requests",
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

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_prefix="RISKI_EXTRACTOR__",  # only applies to extractor-related fields
        extra="ignore",
    )

    @model_validator(mode="after")
    def _validate_date_range(self):
        if not self.end_date:
            return self
        start = datetime.date.fromisoformat(self.start_date)
        end = datetime.date.fromisoformat(self.end_date)
        if end < start:
            raise ValueError("end_date must be on or after start_date")
        return self

    def print_config(self):
        logger = getLogger()
        logger.debug(
            self.model_dump(
                exclude={
                    "openai_api_key": True,
                    "core": {"db": {"password", "database_url"}},
                    "test": {"db_password", "database_url"},
                }
            )
        )


@lru_cache
def get_config() -> Config:
    """Returns the cached project config instance."""
    return Config()
