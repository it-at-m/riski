# ruff: noqa: E402
from dotenv import load_dotenv
from truststore import inject_into_ssl

load_dotenv()
inject_into_ssl()

from logging import Logger, getLogger

import uvicorn
from app.backend import backend
from app.core.settings import BackendSettings, get_settings

if __name__ == "__main__":
    """Runs the application."""
    logger: Logger = getLogger(__name__)
    settings: BackendSettings = get_settings()
    logger.info("Starting application")
    logger.info(settings.model_dump(mode="json"))
    uvicorn.run(
        app=backend,
        host=settings.server_host,
        port=settings.server_port,
        log_config="logconf.yaml",
    )
