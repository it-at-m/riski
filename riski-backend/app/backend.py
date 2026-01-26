# FastAPI backend creation
from contextlib import asynccontextmanager

from app.api.routers.ag_ui import router as ag_ui_router
from app.api.routers.system import router as systems_router
from app.core.settings import BackendSettings, get_settings
from core.lm.helper import create_embedding_model
from fastapi import FastAPI
from langchain_postgres import PGEngine, PGVectorStore


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings: BackendSettings = get_settings()
    docs_enabled = settings.enable_docs

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.vectorstore, pg_engine = await get_vectorstore(settings)
        yield
        await pg_engine.close()

    app = FastAPI(
        title="RISKI Backend",
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
        version=settings.version,
        lifespan=lifespan,
    )

    app.include_router(systems_router)
    app.include_router(ag_ui_router)

    return app


def get_pgengine(settings) -> PGEngine:
    pg_engine = PGEngine.from_connection_string(url=str(settings.core.db.async_database_url))
    return pg_engine


async def get_vectorstore(settings) -> tuple[PGVectorStore, PGEngine]:
    pg_engine = get_pgengine(settings)
    embedding_model = create_embedding_model(settings)
    vectorstore = await PGVectorStore.create(
        engine=pg_engine,
        table_name="file_with_types",
        embedding_service=embedding_model,
        id_column="db_id",
        content_column="text",
        embedding_column="embed",
        metadata_columns=["id", "name", "size"],
    )
    return vectorstore, pg_engine


backend = create_app()
