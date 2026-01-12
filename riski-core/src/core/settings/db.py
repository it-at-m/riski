from pydantic import BaseModel, Field, PostgresDsn


class DatabaseSettings(BaseModel):
    """
    Database configuration settings.
    """

    # === Postgres Settings ===
    name: str = Field(
        description="Postgres database name",
    )
    user: str = Field(
        description="Postgres username",
    )
    password: str = Field(
        description="Postgres password",
    )
    hostname: str = Field(
        description="Postgres host",
    )
    port: int = Field(
        default=5432,
        description="Postgres port",
    )
    batch_size: int = Field(
        default=100,
        description="Batch size for database operations",
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
