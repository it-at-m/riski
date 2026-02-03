from urllib.parse import quote

from pydantic import BaseModel, Field, PostgresDsn


class DatabaseSettings(BaseModel):
    """
    Database configuration settings.
    """

    # === Postgres Settings ===
    name: str = Field(
        description="Postgres database name",
        default="example_db",
    )
    user: str = Field(
        description="Postgres username",
        default="postgres",
    )
    password: str = Field(
        description="Postgres password",
        default="<your-password-here>",
    )
    hostname: str = Field(
        description="Postgres host",
        default="localhost",
    )
    port: int = Field(
        description="Postgres port",
        default=5432,
    )
    batch_size: int = Field(
        description="Batch size for database operations",
        default=100,
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
            password=quote(self.password, safe=""),
            host=self.hostname,
            port=self.port,
            path=self.name,
        )

    @property
    def async_database_url(self) -> PostgresDsn:
        """
        Full Postgres connection URL
        """
        return PostgresDsn.build(
            # use asyncpg
            scheme="postgresql+asyncpg",
            username=self.user,
            password=self.password,
            host=self.hostname,
            port=self.port,
            path=self.name,
        )
