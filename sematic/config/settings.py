# Standard Library
import distutils.util
import enum
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional, Type, Union, cast

# Third-party
import yaml

# Sematic
from sematic.abstract_plugin import MissingPluginError, PluginScope, import_plugin
from sematic.config.config_dir import get_config_dir

logger = logging.getLogger(__name__)


DEFAULT_PROFILE = "default"


class AbstractSettingsVar(enum.Enum):
    """
    Abstract base class for lists of settings vars
    """

    pass


PLUGINS_SCOPES_KEY: Literal["scopes"] = "scopes"
PLUGINS_SETTINGS_KEY: Literal["settings"] = "settings"

# Unfortunately we cannot use the above constants to define the literal below
# Literal must be statically defined
PluginsSettings = Dict[Union[Literal["scopes"], Literal["settings"]], Any]


class ProfileSettings(Dict[AbstractSettingsVar, Union[str, PluginsSettings]]):
    """
    Settings for a given profile (e.g. default).
    """

    pass


class Settings(Dict[str, ProfileSettings]):
    """
    Mapping of profile name to ProfileSettings.
    """

    pass


class MissingSettingsError(Exception):
    def __init__(self, missing_settings: AbstractSettingsVar, cli_command: str):
        # TODO #264: this bleeds cli implementations details
        # this message should be set when triaging all exceptions before being surfaced
        # to the user
        message = f"""
Missing setting: {missing_settings.value}

Set it with:

    $ sematic {cli_command} set {missing_settings.value} VALUE
"""
        super().__init__(message)


class MissingPluginSettingsError(Exception):
    def __init__(self, plugin_name: str, missing_setting_name: str):
        message = f"""
Missing setting: {missing_setting_name} for plugin {plugin_name}.

See https://docs.sematic.dev/plugins.
"""

        super().__init__(message)


@dataclass
class SettingsScope:
    """
    Dataclass to contain information about a certain settings scope (e.g. user,
    server, etc).

    Instances of this classes also contain the cached settings value.

    Parameters
    ----------
    file_name: str
        Name of the YAML file containing settings value for this scope.

    cli_command: str
        Command to set/get settings values for this scope.

    vars: Type[AbstractSettingsVar]
        Enum of available settings for this scope
    """

    file_name: str
    cli_command: str
    vars: Type[AbstractSettingsVar]
    _settings: Optional[Settings] = field(init=False, default=None)
    _active_settings: Optional[ProfileSettings] = field(init=False, default=None)

    @property
    def settings_file_path(self) -> str:
        """
        Full path of settings YAML file.
        """
        return os.path.join(get_config_dir(), self.file_name)

    def get_settings(self) -> Settings:
        """
        Get and cache content of settings file filtered to available settings
        for this scope.
        """
        if self._settings is None:
            self._settings = _load_settings(self.settings_file_path, self.vars)

        return self._settings

    def get_active_settings(self) -> ProfileSettings:
        """
        Get and cache effective settings value for current profile (default).

        This also applies env var overrides.
        """
        if self._active_settings is None:
            self._active_settings = self.get_settings()[DEFAULT_PROFILE]
            _apply_env_var_overrides(self._active_settings, self.vars)

        return self._active_settings

    def get_active_settings_as_dict(self) -> Dict[str, Union[str, PluginsSettings]]:
        """
        Active settings as a dictionary.
        """
        return {var.value: value for var, value in self.get_active_settings().items()}

    def get_setting(self, var: AbstractSettingsVar, *args) -> str:
        """
        Retrieves and returns the specified settings value, with environment
        override.

        Loads and returns the specified settings value. If it does not exist, it
        falls back on the first optional vararg as a default value. If that does
        not exist, it raises.
        """
        value = self.get_active_settings().get(var)

        if value is not None:
            return str(value)

        if len(args) >= 1:
            return args[0]

        raise MissingSettingsError(var, self.cli_command)

    def get_plugin_settings(self, var: AbstractSettingsVar) -> PluginsSettings:
        value = self.get_active_settings().get(var)

        if not isinstance(value, dict) or set(value) != {
            PLUGINS_SCOPES_KEY,
            PLUGINS_SETTINGS_KEY,
        }:
            raise ValueError(f"{var.value} does not point to a plugins setting group")

        return cast(PluginsSettings, value)

    def import_plugins(self, var: AbstractSettingsVar) -> None:
        plugin_scopes = self.get_plugin_settings(var)[PLUGINS_SCOPES_KEY]

        for plugin_scope in PluginScope:
            if plugin_scope.value not in plugin_scopes:
                continue

            plugin_import_paths = plugin_scopes[plugin_scope.value]
            for plugin_import_path in plugin_import_paths:
                try:
                    import_plugin(plugin_import_path)
                except MissingPluginError:
                    logger.warning(f"Cannot find plugin: {plugin_import_path}")

    def set_setting(self, var: AbstractSettingsVar, value: str) -> None:
        """
        Set value for setting.

        Parameters
        ----------
        var: AbstractSettingsVar
            setting to set
        value: str
            value to set
        """
        if var not in self.vars:
            raise ValueError(f"Unknown setting {var.value}")

        settings = self.get_settings()

        settings[DEFAULT_PROFILE][var] = value

        self.save_settings(settings)

        # Void cache to force refresh
        self._active_settings = None

    def delete_setting(self, var: AbstractSettingsVar) -> None:
        """
        Delete setting value.

        Parameters
        ----------
        var: AbstractSettingsVar
            Setting to delete
        """
        if var not in self.vars:
            raise ValueError(f"Unknown setting {var.value}")

        settings = self.get_settings()

        if var in settings[DEFAULT_PROFILE]:
            del settings[DEFAULT_PROFILE][var]

        self.save_settings(settings)

        # Void cache to force refresh
        self._active_settings = None

    def save_settings(self, settings: Settings) -> None:
        """
        Persists the specified settings to the specified settings file.
        """
        yaml_output = yaml.dump(settings, Dumper=EnumDumper)

        with open(self.settings_file_path, "w") as f:
            f.write(yaml_output)


class EnumDumper(yaml.Dumper):
    """
    Custom Dumper for Enum values.

    It serializes Enums as simple strings so that the values aren't represented as class
    instances with type metadata.

    It also deactivates aliases, avoiding creating referential ids in the resulting yaml
    contents.
    """

    def __init__(self, stream, **kwargs):
        super(EnumDumper, self).__init__(stream, **kwargs)
        self.add_multi_representer(
            enum.Enum, lambda _, var: self.represent_str(str(var.value))
        )

    def ignore_aliases(self, data: Any) -> bool:
        return True


def as_bool(value: Optional[Any]) -> bool:
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


def _normalize_enum(enum_type: Type[AbstractSettingsVar], obj: Any):
    """
    Returns a value belonging to the specified enum which corresponds to the specified
    object, if possible.
    """
    if isinstance(obj, enum_type):
        return obj

    try:
        return enum_type[str(obj)]
    except KeyError:
        return None


def _load_settings(file_path: str, vars: Type[AbstractSettingsVar]) -> Settings:
    """
    Loads the settings from the specified settings file, returning their raw string
    representations, or an empty dict if the file is not found.
    """
    settings = Settings()

    try:
        with open(file_path, "r") as f:
            settings = yaml.load(f, yaml.Loader)

    except FileNotFoundError:
        logger.debug("Settings file %s not found", file_path)

    if settings is None:
        settings = Settings()

    if DEFAULT_PROFILE not in settings:
        settings[DEFAULT_PROFILE] = ProfileSettings()

    # Normalizing settings to only have expected values and format as enum
    for profile_settings in settings.values():
        # Doing this instead of usual .items iteration because we mutate the keys
        # as we go
        for key in list(profile_settings):
            normalized_key = _normalize_enum(vars, key)

            if normalized_key is None:
                logger.warning("Unknown setting: %s", key)
            else:
                profile_settings[normalized_key] = profile_settings[key]

            del profile_settings[key]

    return settings


def _apply_env_var_overrides(
    settings: ProfileSettings, vars: Type[AbstractSettingsVar]
) -> None:
    """
    Apply env var overrides on settings.
    """
    for var in vars:
        key = str(var.value)

        if key in os.environ:
            new_value = os.environ[key]
            logger.debug("Overriding %s with %s", key, new_value)

            settings[var] = new_value


def dump_settings(settings: ProfileSettings) -> str:
    """
    Dumps the specified settings to string.
    """
    return yaml.dump(settings, default_flow_style=False, Dumper=EnumDumper)
