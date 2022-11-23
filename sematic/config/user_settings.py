# Standard Library
import enum
import logging
import os
from dataclasses import asdict, dataclass
from typing import Dict, Optional

# Sematic
from sematic.config.config_dir import USER_SETTINGS_FILE, get_config_dir
from sematic.config.settings import (
    _as_bool,
    _load_settings,
    _normalize_enum,
    _save_settings,
)

logger = logging.getLogger(__name__)

_DEFAULT_PROFILE = "default"


class UserSettingsVar(enum.Enum):
    # Sematic
    SEMATIC_API_ADDRESS = "SEMATIC_API_ADDRESS"
    SEMATIC_API_KEY = "SEMATIC_API_KEY"

    # Snowflake
    SNOWFLAKE_USER = "SNOWFLAKE_USER"
    SNOWFLAKE_PASSWORD = "SNOWFLAKE_PASSWORD"
    SNOWFLAKE_ACCOUNT = "SNOWFLAKE_ACCOUNT"

    # AWS
    AWS_S3_BUCKET = "AWS_S3_BUCKET"


class MissingUserSettingsError(Exception):
    def __init__(self, missing_settings: UserSettingsVar):
        # TODO #264: this bleeds cli implementations details
        # this message should be set when triaging all exceptions before being surfaced
        # to the user
        message = """
Missing settings: {}

Set it with:

    $ sematic settings set {} VALUE
""".format(
            missing_settings.value, missing_settings.value
        )
        super().__init__(message)


@dataclass
class UserSettings:
    """
    The representation of the user's settings.

    Parameters
    ----------
    default: Dict[UserSettingsVar, str]
        The settings for defined for the only currently supported "default" profile.
    """

    default: Dict[UserSettingsVar, str]

    def __post_init__(self):
        """
        Validates the consistency of settings data.

        Raises
        ------
        ValueError:
            There is an incorrect value or state
        """
        user_settings = {}

        for var, value in self.default.items():
            # impose the enums over the settings values
            # the vars are read from the yaml as strings, and we need to normalize them
            normalized_var = _normalize_enum(UserSettingsVar, var)

            if normalized_var is None:
                raise ValueError(f"Unknown user setting {var}!")

            user_settings[normalized_var] = str(value)

        self.default = user_settings

    @classmethod
    def get_default_settings(cls) -> "UserSettings":
        """
        Returns modifiable default settings.
        """
        return UserSettings(default={})

    def get_all_settings(self) -> Dict[UserSettingsVar, str]:
        """
        Returns the all the settings.
        """
        return self.default

    def get(self, var: UserSettingsVar) -> Optional[str]:
        """
        Gets the value for the specified variable, or None, if it does not exist.
        """
        return self.default.get(var)

    def set(self, var: UserSettingsVar, value: str) -> None:
        """
        Sets the specified value for the specified variable.
        """
        if value is None:
            value = ""

        self.default[var] = value

    def delete(self, var: UserSettingsVar) -> None:
        """
        Deletes the specified variable.
        """
        if var not in self.default:
            raise ValueError(f"{var.value} is not present in the settings!")

        del self.default[var]


# global settings cache
_settings: Optional[UserSettings] = None


def _get_user_settings_file() -> str:
    """
    Returns the path to the user settings file according to the configuration.
    """
    return os.path.join(get_config_dir(), USER_SETTINGS_FILE)


def _load_user_settings() -> UserSettings:
    """
    Loads the settings from the configured settings file.
    """
    raw_settings = _load_settings(_get_user_settings_file())

    if raw_settings is None or _DEFAULT_PROFILE not in raw_settings:
        return UserSettings.get_default_settings()

    return UserSettings(**raw_settings)  # type: ignore


def _save_user_settings(settings: UserSettings) -> None:
    """
    Persists the specified settings to the configured settings file.
    """
    _save_settings(_get_user_settings_file(), asdict(settings))


def get_active_user_settings() -> UserSettings:
    """
    Returns all the active user settings, with environment overrides.
    """
    global _settings

    if _settings is None:
        _settings = _load_user_settings()

        # Override with env vars
        for var in UserSettingsVar:
            key = str(var.value)
            if key in os.environ:
                new_value = os.environ[key]
                logger.debug("Overriding %s with %s", key, new_value)
                _settings.set(var, new_value)

    return _settings


def get_active_user_settings_strings() -> Dict[str, str]:
    """
    Returns a safe strings-only representation of the active user settings.
    """
    return {
        str(var.value): str(value)
        for var, value in get_active_user_settings().get_all_settings().items()
    }


def get_user_settings(var: UserSettingsVar, *args) -> str:
    """
    Retrieves and returns the specified settings value, with environment override.

    Loads and returns the specified settings value. If it does not exist, it falls back
    on the first optional vararg as a default value. If that does not exist, it raises.
    """
    value = get_active_user_settings().get(var)

    if value is not None:
        return str(value)

    if len(args) >= 1:
        return args[0]

    raise MissingUserSettingsError(var)


def get_bool_user_settings(var: UserSettingsVar, *args) -> bool:
    """
    Retrieves and returns the specified settings value as a boolean, with environment
    override.

    Loads and returns the specified settings value. If it does not exist, it falls back
    on the first optional vararg as a default value. If that does not exist, it raises.
    """
    return _as_bool(get_user_settings(var, *args))


def set_user_settings(var: UserSettingsVar, value: str) -> None:
    """
    Sets the specifies settings value and persists the settings.
    """
    global _settings

    if _settings is None:
        _settings = _load_user_settings()

    _settings.set(var, value)
    _save_user_settings(_settings)


def delete_user_settings(var: UserSettingsVar) -> None:
    """
    Deletes the specified settings value and persists the settings.
    """
    global _settings

    if _settings is None:
        _settings = _load_user_settings()

    _settings.delete(var)
    _save_user_settings(_settings)
