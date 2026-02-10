from pydantic import BaseModel, Field


class GenAISettings(BaseModel):
    """
    Language model configuration settings.
    """

    embedding_model: str = Field(
        description="Embedding model for Retrieval",
        default="text-embedding-3-large",
    )
    chat_model: str = Field(
        description="Chat model for Agent",
        default="gpt-4.1",
    )
    chat_temperature: float = Field(
        description="Temperature setting for chat model",
        default=0.1,
        le=2.0,
        ge=0.0,
    )
    chat_max_retries: int = Field(
        description="Number of retries for chat model requests",
        default=2,
        ge=0,
    )
