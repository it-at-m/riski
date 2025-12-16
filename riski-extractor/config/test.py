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
    database_url: PostgresDsn | None = Field(
        default=None,
        description="Full test database connection URL",
    )
