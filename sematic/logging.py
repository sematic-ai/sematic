# Standard Library
import logging
import os

# Sematic
from sematic.config.config import get_config


def make_log_config(log_to_disk: bool = False, level: int = logging.INFO):
    log_to_stdout = get_config().server_log_to_stdout or not log_to_disk
    stdout_handler_list = ["stdout"] if log_to_stdout else []
    log_rotation_settings = {
        "formatter": "standard",
        "class": "logging.handlers.RotatingFileHandler",
        "maxBytes": 500 * 2**20,  # 500 MB
        "backupCount": 20,
    }

    handlers = {
        "stdout": {
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    }
    if log_to_disk:
        full_handler_list = ["default", "error"] + stdout_handler_list
        handlers.update(
            {
                "default": dict(
                    level=level,  # type: ignore
                    filename=os.path.join(get_config().config_dir, "access.log"),
                    **log_rotation_settings,  # type: ignore
                ),
                "error": dict(
                    level="ERROR",
                    filename=os.path.join(get_config().config_dir, "error.log"),
                    **log_rotation_settings,  # type: ignore
                ),
            }
        )
    else:
        full_handler_list = stdout_handler_list

    root_logger_config = {"level": level, "handlers": full_handler_list}

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
            "gunicorn.error": {"level": logging.ERROR, "handlers": full_handler_list},
            "gunicorn.access": {"level": level, "handlers": full_handler_list},
        },
    }
    return config
