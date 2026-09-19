"""Structured JSON Logging for ReRun."""
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Custom JSON log formatter for structured audit trails."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include custom fields if passed via extra
        if hasattr(record, "task_id"):
            log_entry["task_id"] = record.task_id
        if hasattr(record, "attempt"):
            log_entry["attempt"] = record.attempt
        if hasattr(record, "agent"):
            log_entry["agent"] = record.agent
        if hasattr(record, "event_type"):
            log_entry["event_type"] = record.event_type
        if hasattr(record, "details"):
            log_entry["details"] = record.details

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logger(name: str = "rerun", level: int = logging.INFO) -> logging.Logger:
    """Configures structured logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

    return logger


logger = setup_logger()
