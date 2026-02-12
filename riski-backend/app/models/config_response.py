from pydantic import BaseModel, Field


class ConfigResponse(BaseModel):
    """Response for the config endpoint."""

    version: str = Field(description="The version of the backend.")
    frontend_version: str = Field(description="The version of the frontend.")
    title: str = Field(description="The title of the application.")
    documentation_url: str = Field(description="The URL to the documentation.")
