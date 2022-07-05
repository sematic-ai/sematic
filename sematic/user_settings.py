# Standard library
import enum
import os
from typing import Dict, Optional

# Third-arty
import yaml

# Sematic
from sematic.config_dir import get_config_dir


_SETTINGS_FILE = "settings.yaml"


Settings = Dict[str, Dict[str, str]]


def _settings_file() -> str:
    return os.path.join(get_config_dir(), _SETTINGS_FILE)


def _load_settings():
    try:
        with open(_settings_file(), "r") as f:
            settings = yaml.load(f, yaml.Loader)
    except FileNotFoundError:
        settings = None

    if settings is None:
        settings = {"default": {}}

    return settings


_settings: Optional[Settings] = None


def get_all_user_settings() -> Dict[str, str]:
    """
    Main API to access stored user settings.
    """
    global _settings

    if _settings is None:
        _settings = _load_settings()

        # Override with env vars
        for var, value in _settings["default"].items():
            _settings["default"][var] = os.environ.get(var, value)

    return _settings["default"]


class SettingsVar(enum.Enum):
    # Sematic
    SEMATIC_API_ADDRESS = "SEMATIC_API_ADDRESS"

    # Snowflake
    SNOWFLAKE_USER = "SNOWFLAKE_USER"
    SNOWFLAKE_PASSWORD = "SNOWFLAKE_PASSWORD"
    SNOWFLAKE_ACCOUNT = "SNOWFLAKE_ACCOUNT"


class MissingSettingsError(Exception):
    pass


def get_user_settings(var: SettingsVar) -> str:
    """
    Main API to access individual settings.
    """
    if var not in SettingsVar.__members__.values():
        raise ValueError(
            "Invalid settings var: {}. Available vars: {}".format(
                repr(var), SettingsVar.__members__.values()
            )
        )

    settings = get_all_user_settings().get(var.value)

    if settings is None:
        raise MissingSettingsError(
            """
Missing settings: {}

Set it with

    $ sematic settings set {} VALUE
""".format(
                var, var
            )
        )

    return settings


def set_user_settings(var: SettingsVar, value: str):
    if var not in SettingsVar.__members__.values():
        raise ValueError(
            "Invalid settings key: {}. Available keys:\n{}".format(
                repr(var),
                "\n".join([m.value for m in SettingsVar.__members__.values()]),
            )
        )

    saved_settings = _load_settings()

    saved_settings["default"][var.value] = value
    yaml_output = yaml.dump(saved_settings, Dumper=yaml.Dumper)

    with open(_settings_file(), "w") as f:
        f.write(yaml_output)
