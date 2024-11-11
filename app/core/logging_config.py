import logging
import os
from logging.config import dictConfig

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

log_file_path = os.path.join(LOG_DIR, "app.log")

logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "default"},
        "file": {
            "class": "logging.FileHandler",
            "filename": log_file_path,
            "formatter": "default",
            "encoding": "utf-8",  # Ensure UTF-8 encoding
        },
    },
    "root": {"level": "DEBUG", "handlers": ["console", "file"]},
}


def setup_logging():
    dictConfig(logging_config)
    logging.getLogger(__name__).info("Logging setup initialized")
