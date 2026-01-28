# ruff: noqa: E402
from logging import Logger, getLogger

import uvicorn
from app.backend import backend
from app.core.settings import BackendSettings, get_settings

if __name__ == "__main__":
    """Runs the application."""
    logger: Logger = getLogger("riski-backend")
    config: BackendSettings = get_settings()
    logger.info("Starting application")
    logger.info(config.model_dump(mode="json"))
    uvicorn.run(backend, host="0.0.0.0", port=8080, log_config="logconf.yaml")
