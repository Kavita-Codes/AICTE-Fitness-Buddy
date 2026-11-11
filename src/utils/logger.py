"""
src/utils/logger.py – Structured application logger with rotating file handler.
"""

from __future__ import annotations

import logging
import logging.handlers
import os
from pathlib import Path


def setup_logger(name: str = "fitness_buddy") -> logging.Logger:
    """Configure and return a named logger."""
    from src.config import get_settings

    settings = get_settings()
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Ensure log directory exists
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(log_level)
    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s – %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # Rotating file handler
    rfh = logging.handlers.RotatingFileHandler(
        str(log_path),
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
        encoding="utf-8",
    )
    rfh.setLevel(log_level)
    rfh.setFormatter(fmt)
    logger.addHandler(rfh)

    return logger


def setup_audit_logger() -> logging.Logger:
    """Configure a separate audit trail logger."""
    from src.config import get_settings

    settings = get_settings()
    audit_path = Path(settings.audit_log_path)
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("audit")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    fmt = logging.Formatter(
        '{"time":"%(asctime)s","level":"%(levelname)s","event":%(message)s}',
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )

    rfh = logging.handlers.RotatingFileHandler(
        str(audit_path),
        maxBytes=10_485_760,
        backupCount=10,
        encoding="utf-8",
    )
    rfh.setFormatter(fmt)
    logger.addHandler(rfh)
    return logger
