# Standard Library
import logging
import os
import pathlib

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG_DIR = ".sematic"
_CONFIG_DIR_OVERRIDE_ENV_VAR = "SEMATIC_CONFIG_DIR"
SERVER_SETTINGS_FILE = "server.yaml"
USER_SETTINGS_FILE = "settings.yaml"
MISSING_SERVER_SETTINGS_TEMPLATE = (
    "\nThe server settings have been split out from the user settings. If a user "
    "settings file is configured, then a server settings file must also be present. "
    "Please create the '%s' file locally and move any server-specific settings from '%s' "
    "to this new file, top-level, without the 'default' qualifier. "
    "For more details please see https://docs.sematic.dev/cli#user-settings and "
    "https://docs.sematic.dev/cli#server-settings\n"
)


def get_config_dir() -> str:
    """
    Build the absolute path to the default config directory.

    The config directory is at the base of the user's home
    typically ~/.sematic, and contains the SQLite DB, server.pid,
    API log files, etc.
    """
    config_dir = os.environ.get(_CONFIG_DIR_OVERRIDE_ENV_VAR, _DEFAULT_CONFIG_DIR)
    config_dir_path = pathlib.Path(config_dir)

    if not config_dir_path.is_absolute():
        home_dir = pathlib.Path.home()
        config_dir_path = home_dir / config_dir_path

    if not config_dir_path.parent.exists():
        raise ValueError(
            f"Cannot use '{config_dir_path.as_posix()}' as Sematic config path because "
            f"'{config_dir_path.parent.as_posix()}' does not exist."
        )

    if os.path.isdir(config_dir_path.as_posix()):
        _check_config_dir_schema(config_dir_path.as_posix())
    else:
        config_dir_path.mkdir()

    return config_dir_path.as_posix()


def _check_config_dir_schema(config_dir_path: str) -> None:
    """
    Validates that the config dir has the expected schema - i.e. has all required files.
    """
    server_file = os.path.join(config_dir_path, SERVER_SETTINGS_FILE)
    server_file_present = os.path.isfile(server_file)
    user_file = os.path.join(config_dir_path, USER_SETTINGS_FILE)
    user_file_present = os.path.isfile(user_file)

    if server_file_present and user_file_present:
        return

    if user_file_present:
        logger.error(MISSING_SERVER_SETTINGS_TEMPLATE, server_file, user_file)
        os._exit(1)
