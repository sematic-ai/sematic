# Standard Library
import enum
import logging
import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

# Third-party
import yaml

# Sematic
from sematic.config_dir import get_config_dir

logger = logging.getLogger(__name__)

_SETTINGS_FILE = "settings.yaml"
_DEFAULT_PROFILE = "default"


class SettingsVar(enum.Enum):
    # Sematic
    SEMATIC_API_ADDRESS = "SEMATIC_API_ADDRESS"
    SEMATIC_WORKER_API_ADDRESS = "SEMATIC_WORKER_API_ADDRESS"
    SEMATIC_API_KEY = "SEMATIC_API_KEY"
    SEMATIC_AUTHENTICATE = "SEMATIC_AUTHENTICATE"
    SEMATIC_AUTHORIZED_EMAIL_DOMAIN = "SEMATIC_AUTHORIZED_EMAIL_DOMAIN"

    # Google
    GOOGLE_OAUTH_CLIENT_ID = "GOOGLE_OAUTH_CLIENT_ID"

    # Github
    GITHUB_OAUTH_CLIENT_ID = "GITHUB_OAUTH_CLIENT_ID"

    # Kubernetes
    KUBERNETES_NAMESPACE = "KUBERNETES_NAMESPACE"

    # Snowflake
    SNOWFLAKE_USER = "SNOWFLAKE_USER"
    SNOWFLAKE_PASSWORD = "SNOWFLAKE_PASSWORD"
    SNOWFLAKE_ACCOUNT = "SNOWFLAKE_ACCOUNT"

    # AWS
    AWS_S3_BUCKET = "AWS_S3_BUCKET"

    # GRAFANA
    GRAFANA_PANEL_URL = "GRAFANA_PANEL_URL"


ProfileSettingsType = Dict[SettingsVar, str]


class SettingsDumper(yaml.Dumper):
    """
    Custom Dumper for `SettingsVar`.

    It serializes `SettingsVar`s as simple strings so that the values aren't represented
    as class instances with type metadata

    It also deactivates aliases, avoiding creating referential ids in the
    resulting yaml contents.
    """

    def __init__(self, stream, **kwargs):
        super(SettingsDumper, self).__init__(stream, **kwargs)
        self.add_multi_representer(
            SettingsVar, lambda _, var: self.represent_str(str(var.value))
        )

    def ignore_aliases(self, data: Any) -> bool:
        return True


class MissingSettingsError(Exception):
    def __init__(self, missing_settings: SettingsVar):
        message = (
            """
Missing settings: {}

Set it with

    $ sematic settings set {} VALUE
"""
        ).format(missing_settings.value, missing_settings.value)

        super().__init__(message)


@dataclass
class UserSettings:
    """
    The representation of the user's settings.

    Parameters
    ----------
    active_profile: str
        The profile whose settings will actually be used
    profiles: Dict[str, ProfileSettingsType]
        The settings for each defined profile
    """

    active_profile: str
    profiles: Dict[str, ProfileSettingsType]

    def __post_init__(self):
        """
        Validates the consistency of profile data.

        Raises
        ------
        ValueError:
            There is an incorrect value or state
        """
        if len(self.active_profile) == 0:
            raise ValueError("The active profile cannot be empty!")

        if len(self.profiles) == 0:
            # be lenient in what you accept, so just fill it in and carry on
            self.profiles = {self.active_profile: {}}
        else:
            if self.active_profile not in self.profiles:
                raise ValueError(
                    f"The '{self.active_profile}' active profile is not present in the "
                    f"listed profiles: {list(self.profiles.keys())}"
                )

        # impose the enums over the settings values
        profiles = list(self.profiles.keys())
        for profile in profiles:
            self.profiles[profile] = {
                SettingsVar[var]: value  # type: ignore
                for var, value in self.profiles[profile].items()
            }

    def get_active_profile_settings(self) -> ProfileSettingsType:
        """
        Returns the settings associated with the active profile.
        """
        return self.profiles[self.active_profile]

    def get_inactive_profiles(self) -> List[str]:
        """
        Returns a list of existing profile names other than the active one.
        """
        return [
            profile
            for profile in self.profiles.keys()
            if profile != self.active_profile
        ]

    def set(self, var: SettingsVar, value: Optional[str]) -> None:
        """
        Sets the specified value for the specified variable, for the active profile.

        Deletes the entry if the value is None.
        """
        active_profile_settings = self.get_active_profile_settings()

        if value is not None:
            active_profile_settings[var] = value
            return

        if var not in active_profile_settings:
            raise ValueError(f"{var.value} is not present in the active profile!")

        del active_profile_settings[var]

    def set_profile(self, profile: str) -> None:
        """
        Sets the currently active profile.
        """
        if len(profile) == 0:
            raise ValueError("The profile name cannot be empty!")

        self.active_profile = profile

        if self.active_profile not in self.profiles:
            self.profiles[self.active_profile] = {}

    def delete_profile(self, profile: str) -> None:
        """
        Deletes the specified profile.
        """
        if len(profile) == 0:
            raise ValueError("The profile name cannot be empty!")

        if profile == self.active_profile:
            raise ValueError(
                "Cannot delete the active profile! Switch to another profile first!"
            )

        if profile not in self.profiles:
            raise ValueError(f"Profile '{profile}' does not exist!")

        del self.profiles[profile]


# global settings cache
_settings: Optional[UserSettings] = None


def _get_settings_file() -> str:
    """
    Returns the path to the settings file according to the user configuration.
    """
    return os.path.join(get_config_dir(), _SETTINGS_FILE)


def _load_settings() -> UserSettings:
    """
    Loads the settings from the configured settings file.
    """
    try:
        with open(_get_settings_file(), "r") as f:
            raw_settings = yaml.load(f, yaml.Loader)

    except FileNotFoundError:
        logger.debug("Settings file %s not found", _get_settings_file())
        return get_default_settings()

    if raw_settings is None:
        return get_default_settings()

    try:
        return UserSettings(**raw_settings)
    except TypeError:
        # the settings file has an older syntax and should be corrected
        settings = UserSettings(
            active_profile=next(iter(raw_settings)), profiles=raw_settings
        )
        _save_settings(settings)
        return settings


def _save_settings(settings: UserSettings) -> None:
    """
    Persists the specified settings to the configured settings file.
    """
    yaml_output = yaml.dump(asdict(settings), Dumper=SettingsDumper)

    with open(_get_settings_file(), "w") as f:
        f.write(yaml_output)


def get_default_settings() -> UserSettings:
    """
    Returns modifiable default settings.
    """
    return UserSettings(
        active_profile=_DEFAULT_PROFILE, profiles={_DEFAULT_PROFILE: {}}
    )


def dump_profile_settings(profile_settings: ProfileSettingsType) -> str:
    """
    Dumps the specified settings to string.
    """
    return yaml.dump(profile_settings, default_flow_style=False, Dumper=SettingsDumper)


def get_profiles() -> Tuple[str, List[str]]:
    """
    Returns the active profile name and the list of inactive profile names.
    """

    global _settings

    if _settings is None:
        _settings = _load_settings()

    return _settings.active_profile, _settings.get_inactive_profiles()


def get_active_user_settings() -> ProfileSettingsType:
    """
    Returns the user settings for the active profile, with environment overrides.
    """
    global _settings

    if _settings is None:
        _settings = _load_settings()
        active_profile_settings = _settings.get_active_profile_settings()

        # Override with env vars
        for var in SettingsVar:
            key = str(var.value)
            if key in os.environ:
                new_value = os.environ[key]
                logger.debug("Overriding %s with %s", key, new_value)
                active_profile_settings[var] = new_value

    return _settings.get_active_profile_settings()


def get_active_user_settings_strings() -> Dict[str, str]:
    """
    Returns a safe strings-only representation of the active user settings.
    """
    return {
        str(var.value): str(value) for var, value in get_active_user_settings().items()
    }


def get_user_settings(var: SettingsVar, *args) -> str:
    """
    Main API to access individual settings.

    Loads and returns the specified setting. If it does not exist, it falls back on the
    first optional vararg as a default value. If that does not exist, it raises.
    """
    profile_settings = get_active_user_settings()
    value = profile_settings.get(var)

    if value is None:
        if len(args) >= 1:
            return args[0]

        raise MissingSettingsError(var)

    return str(value)


def set_user_settings(var: SettingsVar, value: str) -> None:
    """
    Sets the specifies setting value and persists the settings.
    """
    global _settings

    if _settings is None:
        _settings = _load_settings()

    _settings.set(var, value)
    _save_settings(_settings)


def delete_user_settings(var: SettingsVar) -> None:
    """
    Deletes the specified setting value from the active profile and persists the settings.
    """
    global _settings

    if _settings is None:
        _settings = _load_settings()

    _settings.set(var, None)
    _save_settings(_settings)


def set_active_profile(profile: str) -> None:
    """
    Sets the currently active profile and persists the settings.
    """
    global _settings

    if _settings is None:
        _settings = _load_settings()

    _settings.set_profile(profile)
    _save_settings(_settings)


def delete_profile(profile: str) -> None:
    """
    Deletes the specified profile and persists the settings.
    """
    global _settings

    if _settings is None:
        _settings = _load_settings()

    _settings.delete_profile(profile)
    _save_settings(_settings)
