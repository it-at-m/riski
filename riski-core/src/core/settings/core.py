from core.settings.db import DatabaseSettings
from core.settings.genai import GenAISettings
from core.settings.testdb import TestDBSettings
from pydantic import BaseModel, Field


class CoreSettings(BaseModel):
    db: DatabaseSettings = Field(
        description="Postgres related settings",
        default_factory=lambda: DatabaseSettings(),
    )

    genai: GenAISettings = Field(
        description="Language model related settings",
        default_factory=lambda: GenAISettings(),
    )

    testdb: TestDBSettings = Field(
        description="Test DB related settings",
        default_factory=lambda: TestDBSettings(),
    )
