# Standard library
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import os
from urllib.parse import urljoin
from typing import Optional

# Sematic
from sematic.config_dir import get_config_dir
from sematic.user_settings import MissingSettingsError, SettingsVar, get_user_settings


def _get_migrations_dir() -> str:
    """
    Build the absolute path to the migrations directory.
    """
    return os.path.join(_get_base_dir(), "db", "migrations")


def _get_base_dir() -> str:
    """
    Build absolute path of directory where examples are stored.
    """
    return os.path.dirname(os.path.realpath(__file__))


EXAMPLES_DIR = "examples"


def _get_examples_dir() -> str:
    """
    Build absolute path to the directory holding examples.
    """
    return os.path.join(_get_base_dir(), EXAMPLES_DIR)


def _get_data_dir() -> str:
    """
    Build the absolute path to the data dir where plots and large payloads
    are stored.
    """
    data_dir = os.path.join(get_config_dir(), "data")

    try:
        os.mkdir(data_dir)
    except FileExistsError:
        pass

    return data_dir


@dataclass
class Config:
    """
    Base Config class to store application configs.
    """

    server_address: str
    api_version: int
    port: int
    db_url: str
    config_dir: str = get_config_dir()
    migrations_dir: str = _get_migrations_dir()
    base_dir: str = _get_base_dir()
    examples_dir: str = _get_examples_dir()
    project_template_dir: str = "{}/template".format(_get_examples_dir())
    data_dir: str = _get_data_dir()

    @property
    def server_url(self) -> str:
        return "http://{}:{}".format(self.server_address, self.port)

    @property
    def api_url(self):
        return urljoin(
            self.server_url,
            "api/v{}".format(self.api_version),
        )

    @property
    def server_pid_file_path(self):
        return os.path.join(self.config_dir, "server.pid")


_SQLITE_FILE = "db.sqlite3"

# Local API server
# SQlite DB
_LOCAL_CONFIG = Config(
    # If choosing localhost, the React app will not be able
    # To proxy requests to the socker io server. Unsure why.
    server_address="127.0.0.1",
    port=5001,
    api_version=1,
    db_url="sqlite:///{}/{}".format(get_config_dir(), _SQLITE_FILE),
)


_CLOUD_CONFIG = Config(
    server_address="0.0.0.0",
    api_version=1,
    port=80,
    db_url=os.environ.get("DATABASE_URL", "NO_DB"),
)


class UserOverrideConfig(Config):
    @property
    def server_url(self) -> str:
        try:
            return get_user_settings(SettingsVar.SEMATIC_API_ADDRESS)
        except MissingSettingsError:
            return "http://{}:{}".format(self.server_address, self.port)


_USER_OVERRIDE_CONFIG = UserOverrideConfig(**asdict(_LOCAL_CONFIG))


class EnvironmentConfigurations(Enum):
    local = _LOCAL_CONFIG
    cloud = _CLOUD_CONFIG
    user = _USER_OVERRIDE_CONFIG


_active_config: Config = EnvironmentConfigurations.user.value


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
