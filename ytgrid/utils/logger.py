"""
Logger Module for YTGrid (Version 3)

This module sets up logging with a standardized format and provides helper functions for logging
information and error messages. Logs are output to both the console and a file named 'ytgrid.log'.
"""

import logging

# Configure logging: output to both a file and the console.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    handlers=[
        logging.FileHandler("ytgrid.log"),
        logging.StreamHandler()
    ]
)


def log_info(message: str) -> None:
    """
    Log an informational message.
    
    :param message: The message to log.
    """
    logging.info(message)


def log_error(message: str) -> None:
    """
    Log an error message.
    
    :param message: The error message to log.
    """
    logging.error(message)
