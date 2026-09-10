import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Optional

# Global context variable to store correlation/request ID for the current async task
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def get_request_id() -> Optional[str]:
    """Retrieve the request ID for the current execution context."""
    return request_id_ctx.get()


class RequestIdFilter(logging.Filter):
    """Logging filter that injects the current request_id into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        return True


class StructuredJsonFormatter(logging.Formatter):
    """
    JSON log formatter for production environments.
    Produces single-line structured JSON logs parseable by log aggregators (ELK, Datadog, CloudWatch).
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", None)
            or get_request_id()
            or "-",
            "message": record.getMessage(),
        }

        # Include structured HTTP metadata if attached to record
        for key in ("method", "path", "status_code", "process_time", "client_ip"):
            if hasattr(record, key):
                log_record[key] = getattr(record, key)

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


def setup_logging(log_level: str = "INFO", log_format: str = "console") -> None:
    """
    Configures application-wide logging with request ID injection and format selection.

    :param log_level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
    :param log_format: 'console' for human-readable development output, 'json' for structured JSON.
    """
    # Fix Windows console encoding for UTF-8 characters/emojis
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())

    # Clear existing handlers to prevent duplicate lines
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIdFilter())

    if log_format.lower() == "json":
        handler.setFormatter(StructuredJsonFormatter())
    else:
        # Human-friendly console format with request_id
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-7s | [%(request_id)s] | %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

    root_logger.addHandler(handler)
