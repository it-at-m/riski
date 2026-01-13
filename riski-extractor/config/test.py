from pydantic import BaseModel, Field, PostgresDsn


class TestSettings(BaseModel):
    # === Test Database (Optional) ===
    db_name: str | None = Field(
        default=None,
        description="Test database name",
    )
    db_user: str | None = Field(
        default=None,
        description="Test database username",
    )
    db_password: str | None = Field(
        default=None,
        description="Test database password",
    )
    db_port: int | None = Field(
        default=5432,
        description="Test database port",
    )
    db_hostname: str | None = Field(
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
            username=self.db_user,
            password=self.db_password,
            host=self.db_hostname,
            port=self.db_port,
            path=self.db_name,
        )
