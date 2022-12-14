# Standard Library
from typing import Dict

# Sematic
from sematic.config.settings import (
    AbstractSettingsVar,
    ProfileSettings,
    SettingsScope,
    as_bool,
)


class UserSettingsVar(AbstractSettingsVar):
    # Sematic
    SEMATIC_API_ADDRESS = "SEMATIC_API_ADDRESS"
    SEMATIC_API_KEY = "SEMATIC_API_KEY"

    # Snowflake
    SNOWFLAKE_USER = "SNOWFLAKE_USER"
    SNOWFLAKE_PASSWORD = "SNOWFLAKE_PASSWORD"
    SNOWFLAKE_ACCOUNT = "SNOWFLAKE_ACCOUNT"

    # AWS
    AWS_S3_BUCKET = "AWS_S3_BUCKET"


CLI_COMMAND = "settings"

_USER_SETTINGS_SCOPE = SettingsScope(
    file_name="settings.yaml",
    cli_command=CLI_COMMAND,
    vars=UserSettingsVar,
)


def get_user_settings_scope() -> SettingsScope:
    return _USER_SETTINGS_SCOPE


def get_active_user_settings_strings() -> Dict[str, str]:
    """
    Returns a safe strings-only representation of the active user settings.
    """
    return _USER_SETTINGS_SCOPE.get_active_settings_as_dict()


def get_active_user_settings() -> ProfileSettings:
    return _USER_SETTINGS_SCOPE.get_active_settings()


def get_user_setting(var: UserSettingsVar, *args) -> str:
    """
    Retrieves and returns the specified settings value, with environment override.

    Loads and returns the specified settings value. If it does not exist, it falls back
    on the first optional vararg as a default value. If that does not exist, it raises.
    """
    return _USER_SETTINGS_SCOPE.get_setting(var, *args)


def get_bool_user_setting(var: UserSettingsVar, *args) -> bool:
    """
    Retrieves and returns the specified settings value as a boolean, with environment
    override.

    Loads and returns the specified settings value. If it does not exist, it falls back
    on the first optional vararg as a default value. If that does not exist, it raises.
    """
    return as_bool(get_user_setting(var, *args))


def set_user_settings(var: UserSettingsVar, value: str) -> None:
    """
    Sets the specifies settings value and persists the settings.
    """
    _USER_SETTINGS_SCOPE.set_setting(var, value)


def delete_user_settings(var: UserSettingsVar) -> None:
    """
    Deletes the specified settings value and persists the settings.
    """
    _USER_SETTINGS_SCOPE.delete_setting(var)


def get_user_settings_file_path() -> str:
    """
    Required for automated migration
    """
    return _USER_SETTINGS_SCOPE.settings_file_path
