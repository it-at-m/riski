from pydantic import BaseModel, Field


class ConfigResponse(BaseModel):
    """Response for the config endpoint."""

    version: str = Field(description="The version of the backend.")
    frontend_version: str = Field(description="The version of the frontend.")
    title: str = Field(description="The title of the application.")
    documentation_url: str = Field(description="The URL to the documentation.")
    contact_url: str = Field(description="The URL to the contact page for inquiries regarding RISKI service.")
    impressum_url: str = Field(description="The URL to the legal notice (Impressum) for RISKI service.")
    townhallbulletin_url: str = Field(description="The URL to the Town Hall Bulletin service information.")
