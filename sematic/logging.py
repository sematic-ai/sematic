# Standard Library
import logging
import os

# Sematic
from sematic.config.config import get_config

_LOG_FILE_ROTATION_SETTINGS = {
    "formatter": "standard",
    "class": "logging.handlers.RotatingFileHandler",
    "maxBytes": 500 * 2**20,  # 500 MB
    "backupCount": 20,
}


def make_log_config(log_to_disk: bool = False, level: int = logging.INFO):
    handlers = {
        "stdout": {
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    }

    if log_to_disk:
        handlers.update(
            {
                "default": dict(
                    level=level,  # type: ignore
                    filename=os.path.join(get_config().config_dir, "access.log"),
                    **_LOG_FILE_ROTATION_SETTINGS,  # type: ignore
                ),
                "error": dict(
                    level="ERROR",
                    filename=os.path.join(get_config().config_dir, "error.log"),
                    **_LOG_FILE_ROTATION_SETTINGS,  # type: ignore
                ),
            }
        )

    handler_names = list(handlers.keys())
    root_logger_config = {"level": level, "handlers": handler_names, "propagate": False}

    config = {
        "version": 1,
        "root": root_logger_config,
        "disable_existing_loggers": True,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            },
        },
        "handlers": handlers,
        "loggers": {
            "sematic": root_logger_config,
            "gunicorn.error": {"level": logging.ERROR, "handlers": handler_names},
            "gunicorn.access": {"level": level, "handlers": handler_names},
        },
    }

    return config
