# ruff: noqa: E402
from dotenv import load_dotenv
from truststore import inject_into_ssl

load_dotenv()
inject_into_ssl()

from logging import getLogger

import uvicorn
from app.backend import backend
from app.settings import get_settings

logger = getLogger(__name__)


if __name__ == "__main__":
    settings = get_settings()
    logger.info("Starting RISKI OParl API on %s:%s", settings.server_host, settings.server_port)
    uvicorn.run(
        app=backend,
        host=settings.server_host,
        port=settings.server_port,
    )
