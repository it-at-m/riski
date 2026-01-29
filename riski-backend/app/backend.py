# FastAPI backend creation
from contextlib import asynccontextmanager

from app.agent import get_riski_agent
from app.api.routers.ag_ui import router as ag_ui_router
from app.api.routers.system import router as systems_router
from app.core.settings import BackendSettings, get_settings
from app.utils.logging import getLogger
from core.lm.helper import create_embedding_model
from fastapi import FastAPI
from langchain_postgres import PGEngine, PGVectorStore
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import text

logger = getLogger()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings: BackendSettings = get_settings()
    docs_enabled = settings.enable_docs

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("Create database connection")
        db_engine = create_async_engine(str(settings.core.db.async_database_url), echo=True, pool_timeout=10, connect_args={"timeout": 30})
        import asyncio

        logger.info("current loop id = %s", id(asyncio.get_running_loop()))
        db_sessionmaker = async_sessionmaker(
            db_engine,
            expire_on_commit=False,
        )
        logger.info("Create vectorstore")
        vectorstore, pg_engine = await get_vectorstore(settings)
        logger.info("Create agent")
        app.state.agent = get_riski_agent(vectorstore, db_sessionmaker)
        # initial db call to establish connection (longer waiting time for first request)
        logger.info("Run initial DB connection test")
        async with db_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Setup on startup complete")
        yield
        await pg_engine.close()
        await db_engine.dispose()

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
        table_name="file",
        embedding_service=embedding_model,
        id_column="db_id",
        content_column="text",
        embedding_column="embed",
        metadata_columns=["id", "name", "size"],
    )
    return vectorstore, pg_engine


backend = create_app()
