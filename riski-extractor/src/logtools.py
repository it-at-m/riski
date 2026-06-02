import json
import logging
import logging.config
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from typing import Iterator

from yaml import safe_load

_log_url: ContextVar[str | None] = ContextVar("log_url", default=None)


def set_log_url(url: str | None) -> None:
    """Set the URL included in subsequent log records for the current context."""
    _log_url.set(url)


def get_log_url() -> str | None:
    """Return the URL currently attached to log records."""
    return _log_url.get()


@contextmanager
def context_log_url(url: str | None) -> Iterator[None]:
    """Temporarily attach a URL to all log records created in this context."""
    token = _log_url.set(url)
    try:
        yield
    finally:
        _log_url.reset(token)


class UrlContextFilter(logging.Filter):
    """Adds the current URL context to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "url"):
            record.url = get_log_url()
        return True


def getLogger(name: str = "riski-extractor") -> logging.Logger:
    """Configures logging and returns a logger with the specified name.

    Parameters:
    name (str): The name of the logger.

    Returns:
    logging.Logger: The logger with the specified name.
    """
    with open("logconf.yaml", "r", encoding="utf-8") as file:
        log_config = safe_load(file)

    logging.config.dictConfig(log_config)
    return logging.getLogger(name)


class JsonFormatter(logging.Formatter):
    """A custom JSON formatter for logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Formats the log record as a JSON string.

        Parameters:
        record (logging.LogRecord): The log record to format.

        Returns:
        str: The log record as a JSON string.
        """
        #
        log_data = {
            "time": datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S"),
            "level": record.levelname,
            "message": record.getMessage(),
            "name": record.name,
        }

        url = getattr(record, "url", get_log_url())
        if url is not None:
            log_data["url"] = url

        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = str(record.exc_info)

        # Add extra fields if needed
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        return json.dumps(log_data)
