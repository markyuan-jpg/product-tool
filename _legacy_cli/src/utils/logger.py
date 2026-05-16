#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unified logging module for Product Catalog Generator.

Usage:
    from src.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Start processing")
"""
import os
import logging
import sys
from datetime import datetime


# Log directory
LOG_DIR = "logs"
LOG_FILE = "product_tool.log"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _ensure_log_dir():
    """Ensure log directory exists."""
    os.makedirs(LOG_DIR, exist_ok=True)


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Set level
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Format
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    _ensure_log_dir()
    file_path = os.path.join(LOG_DIR, LOG_FILE)
    file_handler = logging.FileHandler(file_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


def set_log_level(level: str):
    """
    Set global log level.
    
    Args:
        level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    """
    level_value = getattr(logging, level.upper(), logging.INFO)
    logging.getLogger().setLevel(level_value)
    for handler in logging.getLogger().handlers:
        handler.setLevel(level_value)


def get_log_file_path() -> str:
    """Get the current log file path."""
    return os.path.join(LOG_DIR, LOG_FILE)


# Convenience function for quick logging
def log_info(message: str):
    """Log an info message."""
    get_logger("product_tool").info(message)


def log_error(message: str):
    """Log an error message."""
    get_logger("product_tool").error(message)


def log_warning(message: str):
    """Log a warning message."""
    get_logger("product_tool").warning(message)


def log_debug(message: str):
    """Log a debug message."""
    get_logger("product_tool").debug(message)