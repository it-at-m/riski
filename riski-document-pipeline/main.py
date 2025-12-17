from core.db.db import init_db
from settings.settings import get_settings
from src.parse.parse import run_ocr_for_documents


def parse():
    settings = get_settings()
    init_db(settings.core.db.database_url)
    run_ocr_for_documents(settings)


if __name__ == "__main__":
    parse()
