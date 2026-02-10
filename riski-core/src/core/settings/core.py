from core.settings.db import DatabaseSettings
from core.settings.kafka import KafkaSettings
from core.settings.genai import GenAISettings
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

    kafka: KafkaSettings = Field(default_factory=lambda: KafkaSettings(), description="Kafka related settings")
