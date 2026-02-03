from functools import lru_cache
from pathlib import Path

from core.settings.base import AppBaseSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class DocPipelineSettings(AppBaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_prefix="RISKI_DOCUMENTS__",  # only applies to doc-pipeline-related fields
    )

    max_documents_to_process: int | None = Field(
        default=None,
        description="Maximum number of documents to OCR per run; None processes all",
    )

    ocr_model_name: str = Field(
        default="mistral-document-ai-2505",
        description="OCR model identifier to use for document processing",
    )

    ocr_batch_size: int = Field(
        default=100,
        description="Batch size for OCR handling",
    )


@lru_cache
def get_settings() -> DocPipelineSettings:
    """Returns the cached project config instance."""
    return DocPipelineSettings()
