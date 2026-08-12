"""
Structured Logging – JSON-formatted, context-aware logger factory.

Features:
  - JSON output for structured log aggregation (DataDog, ELK, CloudWatch).
  - Automatic timestamp in ISO 8601 format.
  - Binds request_id and session_id via contextvars for full traceability.
  - Configurable log level from Settings.
  - Module name captured automatically.

Usage:
    from app.core.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Query processed", extra={"session_id": "abc-123", "latency_ms": 42})
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime

from app.core.config import settings

# ── Context Variables ─────────────────────────────
# These are set per-request by middleware/dependencies and
# automatically included in every log line within that request scope.
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
session_id_ctx: ContextVar[str | None] = ContextVar("session_id", default=None)


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects.

    Output fields:
      - timestamp:  ISO 8601 UTC timestamp.
      - level:      Log level name (INFO, WARNING, ERROR, etc.).
      - module:     Logger name (typically __name__ of the calling module).
      - message:    The log message text.
      - request_id: UUID bound to the current HTTP request (if set).
      - session_id: UUID of the user's chat session (if set).
      - Extra fields from the ``extra`` dict are merged at the top level.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get(),
            "session_id": session_id_ctx.get(),
        }

        # Merge any extra fields passed via logger.info(..., extra={...})
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if key not in (
                    "name",
                    "msg",
                    "args",
                    "created",
                    "relativeCreated",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                    "lineno",
                    "funcName",
                    "pathname",
                    "filename",
                    "module",
                    "levelno",
                    "levelname",
                    "thread",
                    "threadName",
                    "process",
                    "processName",
                    "getMessage",
                    "message",
                    "msecs",
                    "taskName",
                ):
                    log_entry[key] = value

        # Include exception traceback if present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


def _setup_root_logger() -> None:
    """Configure the root 'app' logger with JSON formatting to stdout."""
    root_logger = logging.getLogger("app")

    # Prevent duplicate handler attachment on module reload
    if root_logger.handlers:
        return

    log_level = logging.DEBUG if settings.APP_DEBUG else logging.INFO
    root_logger.setLevel(log_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)

    # Prevent log propagation to the default uvicorn handler
    root_logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Factory function returning a child logger under the 'app' namespace.

    Args:
        name: Typically ``__name__`` of the calling module.

    Returns:
        A ``logging.Logger`` instance configured with JSON formatting.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Health check passed")
    """
    _setup_root_logger()
    return logging.getLogger(f"app.{name}")
