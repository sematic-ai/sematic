# Standard Library
import logging
import os
from typing import Union

# Third-party
import flask

# Sematic
from sematic.config.config import get_config


_LOG_FILE_ROTATION_SETTINGS = {
    "formatter": "standard",
    "class": "logging.handlers.RotatingFileHandler",
    "maxBytes": 500 * 2**20,  # 500 MB
    "backupCount": 20,
}


REQUEST_ID_HEADER = "X-REQUEST-ID"


class FlaskRequestContextFilter(logging.Filter):
    def filter(self, record):
        try:
            record.request_id = flask.request.headers.get(REQUEST_ID_HEADER, "")
        except Exception:
            record.request_id = ""
        return True


def make_log_config(log_to_disk: bool = False, level: Union[int, str] = logging.INFO):
    if isinstance(level, str):
        level = level.upper()
    level = logging._checkLevel(level)  # type: ignore

    handlers = {
        "stdout": {
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "filters": ["request_context"],
        },
    }

    if log_to_disk:
        handlers.update(
            {
                "default": dict(
                    level=level,  # type: ignore
                    filters=["request_context"],
                    filename=os.path.join(get_config().config_dir, "access.log"),
                    **_LOG_FILE_ROTATION_SETTINGS,  # type: ignore
                ),
                "error": dict(
                    level="WARNING",
                    filters=["request_context"],
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
                "format": (
                    "%(asctime)s %(request_id)s " "[%(levelname)s] %(name)s: %(message)s"
                ),
            },
        },
        "filters": {
            "request_context": {
                "()": f"{__name__}.{FlaskRequestContextFilter.__name__}",
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
