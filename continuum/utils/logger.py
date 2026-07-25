"""Shared logging configuration for CONTINUUM.

Every other module does `logger = logging.getLogger(__name__)` at import
time, which is a no-op until the root logger is actually configured.
Call configure_logging() once, early in main.py / mcp/server.py, so all
of those module-level loggers actually produce output.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    fmt: str = DEFAULT_FORMAT,
    date_fmt: str = DEFAULT_DATE_FORMAT,
) -> None:
    """Configure the root logger for the whole application.

    Safe to call more than once — existing handlers are cleared first,
    so repeated calls (e.g. in tests) don't produce duplicate log lines.

    Args:
        level: Minimum log level to emit (default: INFO).
        log_file: If given, also write logs to this file path (directory
            is created if it doesn't exist), in addition to stdout.
        fmt: Log message format string.
        date_fmt: Timestamp format string.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear any existing handlers so re-configuring doesn't duplicate output.
    root_logger.handlers.clear()

    formatter = logging.Formatter(fmt=fmt, datefmt=date_fmt)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    logging.getLogger(__name__).debug("Logging configured (level=%s)", logging.getLevelName(level))


def setup_logger(
    name: Optional[str] = None,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """Backward-compatible alias expected by some project scaffolding.

    Configures the root logger (same as configure_logging) and returns
    a logger for the given name (or the root logger if name is None).

    Args:
        name: Logger name to return, e.g. __name__ of the calling module.
        level: Minimum log level to emit.
        log_file: Optional file path to also log to.

    Returns:
        A configured logging.Logger instance.
    """
    configure_logging(level=level, log_file=log_file)
    return logging.getLogger(name)