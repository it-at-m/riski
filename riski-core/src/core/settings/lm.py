from pydantic import BaseModel, Field


class LanguageModelSettings(BaseModel):
    """
    Language model configuration settings.
    """

    embedding_model: str = Field(
        default="text-embedding-3-large",
        description="embedding model to use",
    )
