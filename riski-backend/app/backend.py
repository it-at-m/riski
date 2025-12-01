# FastAPI backend creation
from app.api.routers.ag_ui import router as ag_ui_router
from app.api.routers.system import router as systems_router
from app.core.settings import get_settings
from fastapi import FastAPI

settings = get_settings()
docs_enabled = settings.enable_docs

backend = FastAPI(
    title="RISKI Backend",
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    openapi_url="/openapi.json" if docs_enabled else None,
    version=settings.version,
)

backend.include_router(systems_router)
backend.include_router(ag_ui_router)
