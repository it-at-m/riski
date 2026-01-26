from pydantic import BaseModel, Field


class KafkaSettings(BaseModel):
    """
    Kafka configuration settings.
    """

    # === Kafka Settings ===
    server: str = Field(
        description="Kafka Server URL",
    )
    topic: str = Field(
        default="lhm-riski-parse",
        description="Kafka Topic Name",
    )
    security: bool = Field(
        description="Enable mTLS security for accessing Kafka Server",
    )
    ca_b64: str | None = Field(
        default=None,
        description="Kafka Server CA (B64 Encoded)",
    )
    pkcs12_data: str | None = Field(
        default=None,
        description="Kafka P12 (B64 Encoded)",
    )
    pkcs12_pw: str | None = Field(
        default=None,
        description="Kafka P12 Password (B64 Encoded)",
    )
