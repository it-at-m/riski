# FastAPI backend creation
from contextlib import asynccontextmanager

from app.api.routers.ag_ui import router as ag_ui_router
from app.api.routers.system import router as systems_router
from app.core.settings import get_settings
from fastapi import FastAPI
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGEngine, PGVectorStore

settings = get_settings()
docs_enabled = settings.enable_docs


@asynccontextmanager
async def lifespan(app: FastAPI):
    pg_engine = PGEngine.from_connection_string(url=str(settings.core.db.async_database_url))
    api_key = settings.openai_api_key
    server_url = settings.openai_api_base
    embedding_model = OpenAIEmbeddings(
        model=settings.core.lm.embedding_model,
        base_url=server_url,
        api_key=api_key,
        dimensions=settings.core.lm.embedding_dimension,
    )
    app.state.vectorstore = await PGVectorStore.create(
        engine=pg_engine,
        table_name="file",
        embedding_service=embedding_model,
        id_column="db_id",
        content_column="text",
        embedding_column="embed",
        metadata_columns=["id", "name"],
    )
    yield
    pg_engine.close()


backend = FastAPI(
    title="RISKI Backend",
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    openapi_url="/openapi.json" if docs_enabled else None,
    version=settings.version,
    lifespan=lifespan,
)

backend.include_router(systems_router)
backend.include_router(ag_ui_router)
