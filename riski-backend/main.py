# ruff: noqa: E402
from logging import Logger, getLogger
from app.core.settings import get_settings, Settings
import uvicorn
from dotenv import load_dotenv
from truststore import inject_into_ssl


load_dotenv()
inject_into_ssl()


from app.backend import backend

if __name__ == "__main__":
    """Runs the application."""
    logger: Logger = getLogger("riski-backend")
    config: Settings = get_settings()
    logger.info("Starting application")
    logger.info(config.model_dump())
    uvicorn.run(backend, host="0.0.0.0", port=8080, log_config="logconf.yaml")
