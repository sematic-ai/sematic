import os
import pathlib


_DEFAULT_CONFIG_DIR = ".sematic"


def get_config_dir() -> str:
    """
    Build the absolute path to the default config directory.

    The config directory is at the base of the user's home
    typically ~/.sematic, and contains the SQLite DB, server.pid,
    API log files, etc.
    """
    home_dir = pathlib.Path.home()
    config_dir = os.path.join(home_dir, _DEFAULT_CONFIG_DIR)
    try:
        os.mkdir(config_dir)
    except FileExistsError:
        pass

    return config_dir
