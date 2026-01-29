from langchain_openai import OpenAIEmbeddings

from core.model.data_models import VECTOR_DIM
from core.settings.base import AppBaseSettings


def create_embedding_model(settings: AppBaseSettings) -> OpenAIEmbeddings:
    embedding_model = OpenAIEmbeddings(
        model=settings.core.genai.embedding_model,
    )
    test_embedding = embedding_model.embed_query("test")
    assert len(test_embedding) == VECTOR_DIM
    return embedding_model
