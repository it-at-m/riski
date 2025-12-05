from logging import Logger

from app.utils.logging import getLogger
from langfuse import get_client
from langfuse.langchain import CallbackHandler

logger: Logger = getLogger()
langfuse = get_client()
# Verify connection
if langfuse.auth_check():
    logger.info("Langfuse client is authenticated and ready!")
else:
    logger.error("Authentication failed. Please check your credentials and host.")

# Initialize Langfuse CallbackHandler for Traicing
langfuse_handler = CallbackHandler()
