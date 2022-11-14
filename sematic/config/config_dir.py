# Standard Library
import os
import pathlib

_DEFAULT_CONFIG_DIR = ".sematic"
_CONFIG_DIR_OVERRIDE_ENV_VAR = "SEMATIC_CONFIG_DIR"


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
    try:
        config_dir_path.mkdir()
    except FileExistsError:
        pass

    return config_dir_path.as_posix()
