from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """Response for the health check endpoint."""

    status: str = Field(description="The status of the backend.", default="ok")
    version: str = Field(description="The version of the backend.", examples=["v0.1.0"])
