"""Logging configuration module.

This module provides logging configuration for the FluidNC LED Screen
application.
"""

import logging
from logging.handlers import RotatingFileHandler


def setup_logging(
    log_file: str = "fluidnc_ledscreen.log",
    max_bytes: int = 1024 * 1024,  # 1MB
    backup_count: int = 5,
) -> logging.Logger:
    """Set up logging configuration.

    Args:
        log_file: Path to log file
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("fluidnc_ledscreen")
    logger.setLevel(logging.DEBUG)

    # Create handlers
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
    )
    console_handler = logging.StreamHandler()

    # Create formatters and add it to handlers
    fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_format = logging.Formatter(fmt)
    file_handler.setFormatter(log_format)
    console_handler.setFormatter(log_format)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
