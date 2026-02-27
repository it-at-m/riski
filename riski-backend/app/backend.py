# FastAPI backend creation
from contextlib import asynccontextmanager

from app.agent import build_agent
from app.api.routers.ag_ui import router as ag_ui_router
from app.api.routers.system import router as systems_router
from app.core.observer import setup_langfuse
from app.core.settings import BackendSettings, get_settings
from app.utils.logging import getLogger
from core.genai import create_embedding_model
from fastapi import FastAPI
from langchain_postgres import PGEngine, PGVectorStore
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlmodel import text

logger = getLogger()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings: BackendSettings = get_settings()
    docs_enabled = settings.enable_docs

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Setup database connection
        logger.info(msg="Starting up application and creating database handler")
        db_engine: AsyncEngine = create_async_engine(
            url=settings.core.db.async_database_url.encoded_string(),
            echo=True,
            pool_timeout=10,
            pool_pre_ping=True,
            pool_recycle=1800,
            connect_args={"timeout": 30},
        )

        db_sessionmaker: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=db_engine,
            expire_on_commit=False,
        )
        vectorstore, pg_engine = await build_vectorstore(settings)
        logger.info("Database handler created")

        lf_client, lf_callback_handler = setup_langfuse()

        # Build and assign the agent
        logger.info("Setting up the agent")
        app.state.agent = await build_agent(
            vectorstore=vectorstore,
            db_sessionmaker=db_sessionmaker,
            callbacks=[lf_callback_handler],
            lf_client=lf_client,
        )
        logger.info("Agent setup complete")

        # initial db call to establish connection (longer waiting time for first request)
        logger.info("Running initial DB connection test")
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
    pg_engine = PGEngine.from_connection_string(url=settings.core.db.async_database_url.encoded_string())
    return pg_engine


async def build_vectorstore(settings) -> tuple[PGVectorStore, PGEngine]:
    pg_engine = get_pgengine(settings)
    embedding_model = create_embedding_model(settings)
    vectorstore = await PGVectorStore.create(
        engine=pg_engine,
        schema_name=settings.core.db.schemaname,
        table_name="file",
        embedding_service=embedding_model,
        id_column="db_id",
        content_column="text",
        embedding_column="embed",
        metadata_columns=["id", "name", "size"],
    )
    return vectorstore, pg_engine


backend = create_app()


def get_backend() -> FastAPI:
    """Return the initialized FastAPI application instance."""

    return backend
