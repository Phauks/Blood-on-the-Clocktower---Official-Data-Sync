"""
Centralized logging configuration for Blood on the Clocktower scrapers.

Provides consistent logging across all modules with appropriate log levels.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Log levels
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    verbose: bool = False
) -> logging.Logger:
    """Configure and return a logger instance.

    Args:
        name: Logger name (usually __name__)
        level: Logging level (default: INFO)
        log_file: Optional file path for log output
        verbose: If True, set level to DEBUG

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Set level
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(level)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Format: "[INFO] module: message"
    formatter = logging.Formatter(
        fmt="[%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get existing logger or create new one with defaults.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
