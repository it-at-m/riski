from core.db.db import init_db

from settings.settings import DocPipelineSettings, get_settings
from src.embed.embed_store import embed_documents
from src.parse.parse import run_ocr_for_documents


def parse():
    settings: DocPipelineSettings = get_settings()
    init_db(settings.core.db.database_url)
    run_ocr_for_documents(settings)
    embed_documents(settings)


if __name__ == "__main__":
    parse()
