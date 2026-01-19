from logging import Logger

from app.utils.logging import getLogger
from langfuse import get_client
from langfuse.langchain import CallbackHandler

logger: Logger = getLogger()
langfuse = get_client()
# Verify connection

try:
    langfuse.auth_check()
    logger.info("Langfuse auth check successful.")
except Exception as e:
    logger.error(f"Langfuse auth check failed with the following error {e}. ")


# Initialize Langfuse CallbackHandler for Tracing
langfuse_handler = CallbackHandler()
