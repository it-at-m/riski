from core.model.data_models import VECTOR_DIM
from core.settings.base import AppBaseSettings
from langchain_openai import OpenAIEmbeddings


def create_embedding_model(settings: AppBaseSettings):
    api_key = settings.openai_api_key
    server_url = settings.openai_api_base
    embedding_model = OpenAIEmbeddings(
        model=settings.core.lm.embedding_model,
        base_url=server_url,
        api_key=api_key,
    )
    test_embedding = embedding_model.embed_query("test")
    assert len(test_embedding) == VECTOR_DIM
    return embedding_model
