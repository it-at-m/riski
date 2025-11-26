from app.core.settings import get_settings
from app.models.health_check_response import HealthCheckResponse
from fastapi import APIRouter

settings = get_settings()

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/healthz", response_model=HealthCheckResponse)
def healthz() -> HealthCheckResponse:
    """Health check endpoint for backend availability and version info."""
    return HealthCheckResponse(version=settings.version)
