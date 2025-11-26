# ruff: noqa: E402
from logging import Logger, getLogger

import uvicorn
from dotenv import load_dotenv
from truststore import inject_into_ssl

load_dotenv()
inject_into_ssl()

from app.backend import backend

if __name__ == "__main__":
    """Runs the application."""
    logger: Logger = getLogger("riski-backend")
    logger.info("Starting application")
    uvicorn.run(backend, host="localhost", port=8080, log_config="logconf.yaml")
