from core.settings.db import DatabaseSettings
from core.settings.kafka import KafkaSettings
from core.settings.lm import LanguageModelSettings
from pydantic import BaseModel, Field


class CoreSettings(BaseModel):
    db: DatabaseSettings = Field(
        default_factory=lambda: DatabaseSettings(),
        description="Postgres related settings",
    )

    lm: LanguageModelSettings = Field(
        default_factory=lambda: LanguageModelSettings(),
        description="Language model related settings",
    )

    kafka: KafkaSettings = Field(default_factory=lambda: KafkaSettings(), description="Kafka related settings")
