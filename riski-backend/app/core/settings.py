from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings for the riski-backend.
    """

    version: str = Field(default="DUMMY FOR GITHUBACTION", description="The version of the riski backend.")
    enable_docs: bool = Field(default=False, description="Is the OpenAPI docs endpoint enabled.")

    # === LLM Settings ===
    llm_api_key: SecretStr = Field(
        default="DUMMY FOR GITHUBACTION",
        validation_alias="OPENAI_API_KEY",
        description="API key for OpenAI",
    )
    llm_api_base: str | None = Field(
        default=None,
        validation_alias="OPENAI_API_BASE",
        description="Base URL for OpenAI API",
    )
    llm_api_version: str | None = Field(
        default=None,
        validation_alias="OPENAI_API_VERSION",
        description="Version of the OpenAI API to use",
    )
    tiktoken_cache_dir: str = Field(
        default="tiktoken_cache",
        validation_alias="TIKTOKEN_CACHE_DIR",
        description="Directory to store tiktoken cache",
    )
    riski_llm_embedding_model: str = Field(
        default="text-embedding-3-large",
        validation_alias="RISKI_OPENAI_EMBEDDING_MODEL",
        description="OpenAI embedding model to use",
    )

    # === Langfuse Settings ===
    langfuse_secret_key: SecretStr | None = Field(
        default=None,
        validation_alias="LANGFUSE_SECRET_KEY",
        description="Secret Key for Langfuse",
    )
    langfuse_public_key: SecretStr | None = Field(
        default=None,
        validation_alias="LANGFUSE_PUBLIC_KEY",
        description="Public Key for Langfuse",
    )
    langfuse_host: str | None = Field(
        default=None,
        validation_alias="LANGFUSE_HOST",
        description="Langfuse host",
    )

    # === Mock Langfuse Agent Settings ===
    mock_retrieval_delay_seconds: float = Field(
        default=0.4,
        validation_alias="MOCK_RETRIEVAL_DELAY_SECONDS",
    )
    mock_response_delay_seconds: float = Field(
        default=0.6,
        validation_alias="MOCK_RESPONSE_DELAY_SECONDS",
    )
    mock_retrieval_node: str = Field(
        default="RETRIEVAL",
        validation_alias="MOCK_RETRIEVAL_NODE",
    )
    mock_generate_node: str = Field(
        default="GENERATE",
        validation_alias="MOCK_GENERATE_NODE",
    )

    model_config = SettingsConfigDict(
        env_prefix="RISKI_BACKEND_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
        cli_parse_args=False,
        cli_kebab_case=True,
        cli_prog_name="riski",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()  # type: ignore
