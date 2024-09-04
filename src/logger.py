# logger.py

"""
This module sets up a logger that outputs log messages to a file.

The logger is set to the DEBUG level, and outputs log messages to a file named debug.log in a directory named logs.
If the logs directory does not exist, it is created, but it should be ignored by git and only stored locally.

The log messages are formatted to include the date and time, the name of the logger, the level of the log message, and the log message itself.
Pytest automatically captures the log messages and prints them in the stdout.
"""

import os
import logging

def setup_logger():
    """
    Sets up a logger that outputs log messages to a file.

    This function creates a logger with the name of the current module, and sets its level to DEBUG.
    It also creates a file handler that outputs log messages to a file named debug.log in a directory named logs.
    If the logs directory does not exist, it is created.
    The log messages are formatted to include the date and time, the name of the logger, the level of the log message, and the log message itself.
    The file handler is added to the logger.
    """
    # Create a logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Create a logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # Define a handler to output log messages to a file
    file_handler = logging.FileHandler("logs/debug.log")
    file_handler.setLevel(logging.DEBUG)

    # Define a formatter to output log messages with date and time
    formatter = logging.Formatter(
        "%(filename)s - %(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)

    # Add file handler to the logger
    logger.addHandler(file_handler)
