from pydantic import BaseModel, Field, PostgresDsn


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
    ca_b64: str = Field(
        description="Kafka Server CA (B64 Encoded)",
    )
    pkcs12_data: str = Field(
        description="Kafka P12 (B64 Encoded)",
    )
    pkcs12_pw: str = Field(
        description="Kafka P12 Password (B64 Encoded)",
    )

    @property
    def database_url(self) -> PostgresDsn:
        """
        Full Postgres connection URL
        """
        return PostgresDsn.build(
            # use psycopg version 3
            scheme="postgresql+psycopg",
            username=self.user,
            password=self.password,
            host=self.hostname,
            port=self.port,
            path=self.name,
        )
