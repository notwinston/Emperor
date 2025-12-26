"""Logging configuration for Emperor AI Assistant."""

import logging
import sys
from typing import Optional

from pythonjsonlogger import jsonlogger

from .config import settings


def setup_logging(name: Optional[str] = None) -> logging.Logger:
    """
    Configure and return a logger instance.

    Args:
        name: Logger name (typically __name__ of calling module)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name or "emperor")

    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Console Handler with readable format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    console_format = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # JSON File Handler (for structured logs in debug mode)
    if settings.debug:
        log_file = settings.data_dir / "logs" / "emperor.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)

        json_format = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(json_format)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Module name (use __name__)

    Returns:
        Logger instance
    """
    return setup_logging(name)
