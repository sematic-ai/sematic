# Standard Library
import functools
from typing import Dict, Tuple, Type, cast

# Sematic
from sematic.abstract_plugin import (
    SEMATIC_PLUGIN_AUTHOR,
    AbstractPlugin,
    AbstractPluginSettingsVar,
)
from sematic.config.settings import (
    MissingSettingsError,
    as_bool,
    delete_plugin_setting,
    get_plugin_setting,
    get_plugin_settings,
    set_plugin_setting,
)


class UserSettingsVar(AbstractPluginSettingsVar):
    # Sematic
    SEMATIC_API_ADDRESS = "SEMATIC_API_ADDRESS"
    SEMATIC_API_KEY = "SEMATIC_API_KEY"
    SEMATIC_LOG_INGESTION_MODE = "SEMATIC_LOG_INGESTION_MODE"

    # Snowflake
    SNOWFLAKE_USER = "SNOWFLAKE_USER"
    SNOWFLAKE_PASSWORD = "SNOWFLAKE_PASSWORD"
    SNOWFLAKE_ACCOUNT = "SNOWFLAKE_ACCOUNT"

    # AWS
    AWS_S3_BUCKET = "AWS_S3_BUCKET"


class UserSettings(AbstractPlugin):
    @staticmethod
    def get_author() -> str:
        return SEMATIC_PLUGIN_AUTHOR

    @staticmethod
    def get_version() -> Tuple[int, int, int]:
        return 0, 1, 0

    @classmethod
    def get_settings_vars(cls) -> Type[AbstractPluginSettingsVar]:
        return UserSettingsVar


def get_active_user_settings() -> Dict[UserSettingsVar, str]:
    try:
        user_settings = get_plugin_settings(UserSettings)
    except MissingSettingsError:
        user_settings = {}

    return cast(Dict[UserSettingsVar, str], user_settings)


def get_active_user_settings_strings() -> Dict[str, str]:
    active_user_settings = get_active_user_settings()
    return {var.value: value for var, value in active_user_settings.items()}


get_user_setting = functools.partial(get_plugin_setting, UserSettings)
set_user_setting = functools.partial(set_plugin_setting, UserSettings)
delete_user_setting = functools.partial(delete_plugin_setting, UserSettings)


def get_bool_user_setting(var: UserSettingsVar, *args) -> bool:
    """
    Retrieves and returns the specified settings value as a boolean, with environment
    override.

    Loads and returns the specified settings value. If it does not exist, it falls back
    on the first optional vararg as a default value. If that does not exist, it raises.
    """
    return as_bool(get_user_setting(var, *args))
