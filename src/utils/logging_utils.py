"""
Logging Utilities Module

This module provides utilities for setting up and managing application logging.
"""

import os
import logging
import logging.handlers
from datetime import datetime
from typing import Optional
import sys


def setup_logging(log_file: Optional[str] = None, log_level: str = "INFO") -> None:
    """
    Set up logging for the application.

    Args:
        log_file: Path to the log file. If None, logs will only go to stdout.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    # Convert log level string to logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers to avoid duplicate logs
    root_logger.handlers = []

    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Always add file handler
    if not log_file:
        log_file = "logs/agent.log"
    
    # Ensure the directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Add rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Log startup message
    root_logger.info(f"Logging initialized at {datetime.now()} with level {log_level}")

    # Configure third-party loggers
    configure_third_party_loggers()


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: The name of the logger
        
    Returns:
        logging.Logger: The logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Set to DEBUG level
    
    # Return the logger if handlers are already set up
    if logger.handlers:
        return logger
        
    # Set up the logging format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
                                '%Y-%m-%d %H:%M:%S')
    
    # Add a file handler
    os.makedirs("logs", exist_ok=True)
    file_handler = logging.FileHandler('logs/agent.log')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)  # Set file handler to DEBUG
    logger.addHandler(file_handler)
    
    # Add a console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)  # Leave console at INFO to avoid too much output
    logger.addHandler(console_handler)
    
    return logger


def log_function_call(logger: logging.Logger, func_name: str, args: tuple = None, kwargs: dict = None) -> None:
    """
    Log a function call with its arguments.

    Args:
        logger: Logger instance.
        func_name: Name of the function being called.
        args: Positional arguments to the function.
        kwargs: Keyword arguments to the function.
    """
    args_str = str(args) if args else "()"
    kwargs_str = str(kwargs) if kwargs else "{}"
    logger.debug(f"Function call: {func_name} with args={args_str} kwargs={kwargs_str}")


def log_exception(logger: logging.Logger, e: Exception, context: str = "") -> None:
    """
    Log an exception with context.

    Args:
        logger: Logger instance.
        e: Exception to log.
        context: Additional context about where the exception occurred.
    """
    if context:
        logger.exception(f"Exception in {context}: {str(e)}")
    else:
        logger.exception(f"Exception: {str(e)}")


def configure_third_party_loggers(level: str = "WARNING") -> None:
    """
    Configure third-party loggers to reduce noise.

    Args:
        level: Logging level for third-party modules.
    """
    numeric_level = getattr(logging, level.upper(), logging.WARNING)

    # Suppress verbose logs from common libraries
    for module in ["requests", "urllib3", "openai", "httpx", "crewai"]:
        logging.getLogger(module).setLevel(numeric_level)