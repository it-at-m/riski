import os
from logging import Logger

from anyio.functools import lru_cache
from app.utils.logging import getLogger
from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler

logger: Logger = getLogger(__name__)


@lru_cache(maxsize=1)
def setup_langfuse() -> tuple[Langfuse, CallbackHandler]:
    langfuse = get_client()
    # Verify connection
    if not os.getenv("LOCAL_DEBUG"):
        try:
            langfuse.auth_check()
            logger.info("Langfuse auth check successful.")
        except Exception as e:
            logger.error(f"Langfuse auth check failed with the following error {e}. ")
            raise e

    # Initialize Langfuse CallbackHandler for Tracing
    langfuse_handler = CallbackHandler()
    return langfuse, langfuse_handler
