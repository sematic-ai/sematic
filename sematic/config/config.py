# Standard Library
import logging
import os
import sqlite3
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Optional
from urllib.parse import urljoin

# Sematic
from sematic.config.config_dir import get_config_dir
from sematic.config.settings import MissingSettingsError
from sematic.config.user_settings import UserSettingsVar, get_user_setting
from sematic.versions import version_as_string

logger = logging.getLogger(__name__)

# Support for dropping columns added in 3.35.0
MIN_SQLITE_VERSION = (3, 35, 0)


def _check_sqlite_version():
    version_tuple = sqlite3.sqlite_version.split(".")

    # get major/minor as ints. Patch can sometimes have non-digit chars
    major, minor = int(version_tuple[0]), int(version_tuple[1])
    if (major, minor) < MIN_SQLITE_VERSION:
        # TODO #302: implement sustainable way to upgrade sqlite3 DBs
        logger.warning(
            "Sematic will soon require the sqlite3 version to be at least %s, but your "
            "Python is using %s. Please upgrade. You may find this useful: "
            "https://stackoverflow.com/a/55729735/2540669",
            version_as_string(MIN_SQLITE_VERSION),
            sqlite3.sqlite_version,
        )


def _get_migrations_dir() -> str:
    """
    Build the absolute path to the migrations directory.
    """
    return os.path.join(_get_base_dir(), "db", "migrations")


def _get_base_dir() -> str:
    """
    Build absolute path of directory where examples are stored.
    """
    config_dir = os.path.dirname(os.path.realpath(__file__))
    base_dir = os.path.join(config_dir, os.pardir)
    return base_dir


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


# Set whenever we're inside a cloud job
ON_WORKER_ENV_VAR = "ON_SEMATIC_WORKER"
KUBERNETES_POD_NAME_ENV_VAR = "KUBERNETES_POD_NAME"
SEMATIC_SERVER_ADDRESS_ENV_VAR = "SEMATIC_SERVER_ADDRESS"
SEMATIC_WORKER_SERVER_ADDRESS_ENV_VAR = "SEMATIC_WORKER_API_ADDRESS"


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
    server_log_to_stdout: bool = False

    @property
    def server_url(self) -> str:
        if self.server_url_is_set_via_env_vars():
            return self.server_url_from_env_vars()
        return "http://{}:{}".format(self.server_address, self.port)

    @property
    def api_url(self) -> str:
        return urljoin(
            self.server_url,
            "api/v{}".format(self.api_version),
        )

    @property
    def server_pid_file_path(self) -> str:
        return os.path.join(self.config_dir, "server.pid")

    def server_url_is_set_via_env_vars(self) -> bool:
        return SEMATIC_SERVER_ADDRESS_ENV_VAR in os.environ or (
            ON_WORKER_ENV_VAR in os.environ
            and SEMATIC_WORKER_SERVER_ADDRESS_ENV_VAR in os.environ
        )

    def server_url_from_env_vars(self) -> str:
        server_address = os.environ.get(SEMATIC_SERVER_ADDRESS_ENV_VAR, None)
        if ON_WORKER_ENV_VAR in os.environ:
            server_address = os.environ.get(
                SEMATIC_WORKER_SERVER_ADDRESS_ENV_VAR, server_address
            )
        if server_address is None:
            raise ValueError(
                f"Cannot construct server URL from env vars if "
                f"{SEMATIC_SERVER_ADDRESS_ENV_VAR} is not set."
            )
        if server_address is not None and (
            server_address.startswith("http://")
            or server_address.startswith("https://")
        ):
            return server_address
        port = os.environ.get("PORT", 80)
        return "http://{}:{}".format(server_address, port)


_SQLITE_FILE = "db.sqlite3"

# Local API server
# SQlite DB
_LOCAL_CONFIG = Config(
    # If choosing localhost, the React app will not be able
    # To proxy requests to the socker io server. Unsure why.
    server_address=os.environ.get(SEMATIC_SERVER_ADDRESS_ENV_VAR, "127.0.0.1"),
    port=int(os.environ.get("PORT", 5001)),
    api_version=1,
    db_url=os.environ.get(
        "DATABASE_URL", "sqlite:///{}/{}".format(get_config_dir(), _SQLITE_FILE)
    ),
    server_log_to_stdout=False,
)


_CLOUD_CONFIG = Config(
    server_address=os.environ.get(SEMATIC_SERVER_ADDRESS_ENV_VAR, "0.0.0.0"),
    api_version=1,
    port=int(os.environ.get("PORT", 80)),
    db_url=os.environ.get("DATABASE_URL", "NO_DB"),
    server_log_to_stdout=True,
)


class UserOverrideConfig(Config):
    @property
    def server_url(self) -> str:
        # environment vars should take precedence over whatever is in the
        # users settings file.
        if self.server_url_is_set_via_env_vars():
            return self.server_url_from_env_vars()

        try:
            return get_user_setting(UserSettingsVar.SEMATIC_API_ADDRESS)
        except MissingSettingsError:
            return "http://{}:{}".format(self.server_address, self.port)


_USER_OVERRIDE_CONFIG = UserOverrideConfig(**asdict(_LOCAL_CONFIG))


class EnvironmentConfigurations(Enum):
    local = _LOCAL_CONFIG
    cloud = _CLOUD_CONFIG
    user = _USER_OVERRIDE_CONFIG


_active_config: Config = EnvironmentConfigurations.user.value


def switch_env(env: str) -> None:
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
    logger.info("Switch to env {} whose config is {}".format(env, get_config()))

    # TODO #302: implement sustainable way to upgrade sqlite3 DBs
    if _active_config.db_url.startswith("sqlite"):
        _check_sqlite_version()


def set_config(config: Config) -> None:
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
