# ruff: noqa: E402
from dotenv import load_dotenv
from truststore import inject_into_ssl

load_dotenv()
inject_into_ssl()

from core.db.db import init_db

from settings.settings import DocPipelineSettings, get_settings
from src.embed.embed_store import embed_documents
from src.logtools import getLogger
from src.parse.parse import run_ocr_for_documents

logger = getLogger()


def document_processing():
    settings: DocPipelineSettings = get_settings()
    init_db(settings.core.db.database_url)
    logger.info("Start parsing text from documents")
    run_ocr_for_documents(settings)
    logger.info("Start embedding parsed document texts")
    embed_documents(settings)
    logger.info("RIS document processing completed successfully")


if __name__ == "__main__":
    document_processing()
