import json
import logging
import logging.config
from datetime import datetime, timezone

from yaml import safe_load


def getLogger(name: str = "zammad-ai") -> logging.Logger:
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

    # Standard LogRecord attributes to exclude
    STANDARD_ATTRIBUTES: set[str] = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "getMessage",
        "message",
    }

    def format(self, record: logging.LogRecord) -> str:
        """Formats the log record as a JSON string.

        Parameters:
            record (logging.LogRecord): The log record to format.

        Returns:
            str: The log record as a JSON string.
        """
        #
        log_data = {
            "time": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "name": record.name,
        }

        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add any extra fields that were passed via the extra parameter

        # Add any attributes that aren't standard LogRecord attributes
        for key, value in record.__dict__.items():
            if key not in self.STANDARD_ATTRIBUTES and not key.startswith("_"):
                log_data[key] = value

        return json.dumps(log_data)
