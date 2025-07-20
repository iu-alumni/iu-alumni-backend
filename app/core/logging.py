import logging
from logging.handlers import RotatingFileHandler
import os
import sys


def setup_logging():
    """Configure logging for the application."""
    # Get environment
    environment = os.getenv("ENVIRONMENT", "DEV").upper()
    is_development = environment == "DEV"

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if is_development else logging.INFO)

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create formatter
    if is_development:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    else:
        # Production: less verbose, no sensitive info
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    if is_development:
        console_handler.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(logging.INFO)

    logger.addHandler(console_handler)

    # File handler for production
    if not is_development:
        file_handler = RotatingFileHandler(
            "app.log",
            maxBytes=10485760,
            backupCount=5,  # 10MB files, keep 5
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)

    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    return logger


# Create application logger
app_logger = logging.getLogger("iu_alumni")
