from pydantic import BaseModel, Field, PostgresDsn


class TestDBSettings(BaseModel):
    # === Test Database (Optional) ===
    name: str | None = Field(
        default=None,
        description="Test database name",
    )
    user: str | None = Field(
        default=None,
        description="Test database username",
    )
    password: str | None = Field(
        default=None,
        description="Test database password",
    )
    port: int | None = Field(
        default=5432,
        description="Test database port",
    )
    hostname: str | None = Field(
        default="localhost",
        description="Test database host",
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
