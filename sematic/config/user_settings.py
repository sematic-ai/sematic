# Standard Library
import distutils.util
import enum
import logging
import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

# Third-party
import yaml

# Sematic
from sematic.config.config_dir import get_config_dir

logger = logging.getLogger(__name__)

_USER_SETTINGS_FILE = "settings.yaml"
_DEFAULT_PROFILE = "default"


class UserSettingsVar(enum.Enum):
    # Server:
    # Sematic
    SEMATIC_AUTHENTICATE = "SEMATIC_AUTHENTICATE"
    SEMATIC_AUTHORIZED_EMAIL_DOMAIN = "SEMATIC_AUTHORIZED_EMAIL_DOMAIN"
    SEMATIC_WORKER_API_ADDRESS = "SEMATIC_WORKER_API_ADDRESS"

    # Google
    GOOGLE_OAUTH_CLIENT_ID = "GOOGLE_OAUTH_CLIENT_ID"

    # Github
    GITHUB_OAUTH_CLIENT_ID = "GITHUB_OAUTH_CLIENT_ID"

    # Kubernetes
    KUBERNETES_NAMESPACE = "KUBERNETES_NAMESPACE"

    # GRAFANA
    GRAFANA_PANEL_URL = "GRAFANA_PANEL_URL"

    # User:
    # Sematic
    SEMATIC_API_ADDRESS = "SEMATIC_API_ADDRESS"
    SEMATIC_API_KEY = "SEMATIC_API_KEY"

    # Snowflake
    SNOWFLAKE_USER = "SNOWFLAKE_USER"
    SNOWFLAKE_PASSWORD = "SNOWFLAKE_PASSWORD"
    SNOWFLAKE_ACCOUNT = "SNOWFLAKE_ACCOUNT"

    # AWS
    AWS_S3_BUCKET = "AWS_S3_BUCKET"


class UserSettingsDumper(yaml.Dumper):
    """
    Custom Dumper for `UserSettingsVar`.

    It serializes `UserSettingsVar`s as simple strings so that the values aren't
    represented as class instances with type metadata.

    It also deactivates aliases, avoiding creating referential ids in the resulting yaml
    contents.
    """

    def __init__(self, stream, **kwargs):
        super(UserSettingsDumper, self).__init__(stream, **kwargs)
        self.add_multi_representer(
            UserSettingsVar, lambda _, var: self.represent_str(str(var.value))
        )

    def ignore_aliases(self, data: Any) -> bool:
        return True


class MissingSettingsError(Exception):
    def __init__(self, missing_settings: UserSettingsVar):
        message = """
Missing settings: {}

Set it with

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
        # impose the enums over the settings values
        # the vars are read from the yaml as strings, and we need to normalize them
        self.default = {
            UserSettings._normalize_var(var): str(value)
            for var, value in self.default.items()
        }

    @classmethod
    def _normalize_var(cls, var: Any):
        return var if isinstance(var, UserSettingsVar) else UserSettingsVar[str(var)]

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


def _as_bool(value: Optional[Any]) -> bool:
    """
    Returns a boolean interpretation of the contents of the specified value.
    """
    if isinstance(value, bool):
        return value

    if value is None:
        return False

    str_value = str(value)
    if len(str_value) == 0:
        return False

    return bool(distutils.util.strtobool(str_value))


def _get_settings_file() -> str:
    """
    Returns the path to the settings file according to the user configuration.
    """
    return os.path.join(get_config_dir(), _USER_SETTINGS_FILE)


def _load_settings() -> UserSettings:
    """
    Loads the settings from the configured settings file.
    """
    try:
        with open(_get_settings_file(), "r") as f:
            raw_settings = yaml.load(f, yaml.Loader)

    except FileNotFoundError:
        logger.debug("Settings file %s not found", _get_settings_file())
        return UserSettings.get_default_settings()

    if raw_settings is None:
        return UserSettings.get_default_settings()

    return UserSettings(**raw_settings)


def _save_settings(settings: UserSettings) -> None:
    """
    Persists the specified settings to the configured settings file.
    """
    yaml_output = yaml.dump(asdict(settings), Dumper=UserSettingsDumper)

    with open(_get_settings_file(), "w") as f:
        f.write(yaml_output)


def dump_settings(settings: UserSettings) -> str:
    """
    Dumps the specified settings to string.
    """
    return yaml.dump(
        settings.default, default_flow_style=False, Dumper=UserSettingsDumper
    )


def get_active_user_settings() -> UserSettings:
    """
    Returns all the active user settings, with environment overrides.
    """
    global _settings

    if _settings is None:
        _settings = _load_settings()

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

    raise MissingSettingsError(var)


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
        _settings = _load_settings()

    _settings.set(var, value)
    _save_settings(_settings)


def delete_user_settings(var: UserSettingsVar) -> None:
    """
    Deletes the specified settings value and persists the settings.
    """
    global _settings

    if _settings is None:
        _settings = _load_settings()

    _settings.delete(var)
    _save_settings(_settings)
