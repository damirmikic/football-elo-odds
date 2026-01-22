"""Logging configuration for the application."""

import logging
import logging.handlers
import os
from pathlib import Path


def setup_logging(
    log_level=logging.INFO,
    log_file="logs/app.log",
    max_bytes=10485760,  # 10MB
    backup_count=5,
):
    """
    Configure logging for the application.

    Args:
        log_level: The logging level (default: INFO)
        log_file: Path to the log file (default: logs/app.log)
        max_bytes: Maximum size of log file before rotation (default: 10MB)
        backup_count: Number of backup files to keep (default: 5)

    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger("football-elo-odds")
    logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    simple_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)

    # Log initial message
    logger.info("Logging configured successfully")

    return logger


def get_logger(name=None):
    """
    Get a logger instance.

    Args:
        name: Optional logger name. If None, returns the root logger.

    Returns:
        logging.Logger: Logger instance
    """
    if name:
        return logging.getLogger(f"football-elo-odds.{name}")
    return logging.getLogger("football-elo-odds")
