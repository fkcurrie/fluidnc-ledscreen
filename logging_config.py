import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    # Configure logging
    logger = logging.getLogger('fluidnc_monitor')
    logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)

    # Add handlers
    logger.addHandler(console_handler)

    return logger 