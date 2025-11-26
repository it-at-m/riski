# FastAPI backend creation
from app.core.settings import get_settings
from app.models.health_check_response import HealthCheckResponse
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


# Health check endpoint
@backend.get("/api/healthz")
def healthz() -> HealthCheckResponse:
    """
    Endpoint for checking the health status of the backend.

    Returns:
        HealthCheckResponse: The health check response including the version and status.
    """
    return HealthCheckResponse(version=settings.version)
