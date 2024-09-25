from logging.config import dictConfig

logging_config = {
    "version": 1,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
        },
    },
    "handlers": {
        "default": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {"level": "INFO", "handlers": ["default"]},
}


def setup_logging():
    dictConfig(logging_config)
