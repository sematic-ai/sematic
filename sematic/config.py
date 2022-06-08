# Standard library
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import os
import pathlib
from urllib.parse import urljoin
from typing import Optional

_DEFAULT_CONFIG_DIR = ".sematic"


def _get_config_dir() -> str:
    home_dir = pathlib.Path.home()
    config_dir = os.path.join(home_dir, _DEFAULT_CONFIG_DIR)
    try:
        os.mkdir(config_dir)
    except FileExistsError:
        pass

    return config_dir


@dataclass
class Config:
    server_address: str
    api_version: int
    port: int
    db_url: str
    config_dir: str = _get_config_dir()

    @property
    def server_url(self) -> str:
        return "http://{}:{}".format(self.server_address, self.port)

    @property
    def api_url(self):
        return urljoin(
            self.server_url,
            "api/v{}".format(self.api_version),
        )


# Local API server
# DB in container
_DEV_CONFIG = Config(
    server_address="0.0.0.0",
    port=5001,
    api_version=1,
    db_url="postgresql://postgres:password@0.0.0.0:5432/sematic",
)


# DB and API in containers
_LOCAL_CONFIG = Config(
    server_address="0.0.0.0",
    port=5002,
    api_version=1,
    db_url="postgresql://postgres:password@0.0.0.0:5432/sematic",
)

# Local API server
# DB in SQLITE file
_LOCAL_SQLITE_CONFIG = Config(
    **(
        asdict(_DEV_CONFIG)  # type: ignore
        | dict(db_url="sqlite:///{}/db.sqlite3".format(_get_config_dir()))
    )
)

# For the API server to run within the container
_CONTAINER_CONFIG = Config(
    server_address="0.0.0.0",
    api_version=1,
    port=5002,
    db_url="postgresql://postgres:password@sematic-postgres:5432/sematic",
)


class EnvironmentConfigurations(Enum):
    local = _LOCAL_CONFIG
    local_sqlite = _LOCAL_SQLITE_CONFIG
    container = _CONTAINER_CONFIG


DEFAULT_ENV = "local"


_active_config: Config = EnvironmentConfigurations[DEFAULT_ENV].value


def switch_env(env: str):
    """
    Switch environment.
    """
    if env not in EnvironmentConfigurations.__members__:
        raise ValueError(
            "Unknown env {}, expecting one of {}".format(
                repr(env), tuple(EnvironmentConfigurations.__members__.keys())
            )
        )

    set_config(EnvironmentConfigurations[env].value)
    logger = logging.getLogger(__name__)
    logger.info("Switch to env {} whose config is {}".format(env, get_config()))


def set_config(config: Config):
    global _active_config
    _active_config = config


def current_env() -> Optional[str]:
    for env, config in EnvironmentConfigurations.__members__.items():
        if get_config() is config.value:
            return env

    return None


def get_config() -> Config:
    """
    Get current configuration.
    """
    global _active_config
    return _active_config
