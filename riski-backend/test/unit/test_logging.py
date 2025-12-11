import json
import logging
import sys
from datetime import datetime

from app.utils.logging import JsonFormatter, getLogger


def test_getLogger_configures_json_formatter():
    """getLogger should load logconf.yaml and attach the JsonFormatter to handlers."""

    logger = getLogger("dev")

    assert logger.level == logging.DEBUG
    assert any(isinstance(handler.formatter, JsonFormatter) for handler in logger.handlers), (
        "Expected at least one handler using the JsonFormatter"
    )


def test_json_formatter_includes_standard_and_extra_fields():
    """JsonFormatter should emit JSON with standard and custom fields."""

    formatter = JsonFormatter()
    logger = logging.getLogger("json-test")

    record = logger.makeRecord(
        "json-test",
        logging.INFO,
        __file__,
        42,
        "Processed %s records",
        (3,),
        None,
        extra={"request_id": "abc-123"},
    )

    payload = json.loads(formatter.format(record))

    assert payload["level"] == "INFO"
    assert payload["message"] == "Processed 3 records"
    assert payload["name"] == "json-test"
    assert payload["request_id"] == "abc-123"
    assert datetime.fromisoformat(payload["time"]).tzinfo is not None


def test_json_formatter_includes_exception_trace():
    """JsonFormatter should serialize exception information when present."""

    formatter = JsonFormatter()
    logger = logging.getLogger("json-test")

    try:
        raise ValueError("boom")
    except ValueError:
        record = logger.makeRecord(
            "json-test",
            logging.ERROR,
            __file__,
            99,
            "Failed",
            (),
            exc_info=sys.exc_info(),
        )

    payload = json.loads(formatter.format(record))

    assert payload["level"] == "ERROR"
    assert "exception" in payload
    assert "ValueError" in payload["exception"]
