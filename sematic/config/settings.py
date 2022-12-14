# Standard Library
import distutils.util
import enum
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type, TypeVar

# Third-party
import yaml

# Sematic
from sematic.abstract_plugin import (
    AbstractPlugin,
    AbstractPluginSettingsVar,
    PluginScope,
    import_plugin,
)
from sematic.config.config_dir import get_config_dir

logger = logging.getLogger(__name__)


DEFAULT_PROFILE = "default"
CURRENT_SETTINGS_SCHEMA_VERSION = 0

PluginScopes = Dict[PluginScope, List[str]]
PluginSettings = Dict[AbstractPluginSettingsVar, str]
PluginsSettings = Dict[str, PluginSettings]


@dataclass
class ProfileSettings:
    scopes: PluginScopes
    settings: PluginsSettings


@dataclass
class Settings:
    version: int
    profiles: Dict[str, ProfileSettings]

    @classmethod
    def make_default(cls):
        return Settings(
            version=CURRENT_SETTINGS_SCHEMA_VERSION,
            profiles={DEFAULT_PROFILE: ProfileSettings(scopes={}, settings={})},
        )


class MissingSettingsError(Exception):
    def __init__(
        self,
        plugin: Type[AbstractPlugin],
        var: Optional[AbstractPluginSettingsVar] = None,
    ):
        # TODO #264: this bleeds cli implementations details
        # this message should be set when triaging all exceptions before being surfaced
        # to the user
        command = (
            "server-settings" if plugin.get_name() == "ServerSettings" else "settings"
        )
        option = (
            ""
            if plugin.get_name() in ("UserSettings", "ServerSettings")
            else f"-p {plugin.get_path()}"
        )
        var_str = "VAR" if var is None else var.value

        message = f"""
Missing setting:

Set it with:

    $ sematic {command} set {var_str} VALUE {option}
"""
        super().__init__(message)


_SETTINGS: Optional[Settings] = None


def get_settings_file_path():
    return os.path.join(get_config_dir(), "settings.yaml")


def get_settings() -> Settings:
    global _SETTINGS

    if _SETTINGS is None:
        _SETTINGS = _load_settings(get_settings_file_path())

    return _SETTINGS


def get_active_settings() -> ProfileSettings:
    global _SETTINGS

    if _SETTINGS is None:
        settings = get_settings()

        profile_settings = settings.profiles[DEFAULT_PROFILE]

        for plugin_path, plugin_settings in profile_settings.settings.items():
            plugin_settings_vars = _get_plugin_settings_vars(plugin_path)
            _apply_env_var_overrides(plugin_settings, plugin_settings_vars)

    return get_settings().profiles[DEFAULT_PROFILE]


def get_active_plugins(
    scope: PluginScope, default: List[Type[AbstractPlugin]]
) -> List[Type[AbstractPlugin]]:
    scopes = get_active_settings().scopes

    if scope not in scopes:
        return default

    imported_plugins = [import_plugin(plugin_path) for plugin_path in scopes[scope]]

    return imported_plugins


def get_plugin_settings(
    plugin: Type[AbstractPlugin],
) -> Dict[AbstractPluginSettingsVar, str]:
    settings = get_active_settings().settings

    plugin_path = plugin.get_path()

    if plugin_path not in settings:
        raise MissingSettingsError(plugin)

    return settings[plugin_path]


def get_plugin_setting(
    plugin: Type[AbstractPlugin], var: AbstractPluginSettingsVar, *args
) -> str:
    try:
        plugin_settings = get_plugin_settings(plugin)
    except MissingSettingsError:
        plugin_settings = {}

    if var not in plugin_settings:
        if len(args) > 0:
            return args[0]

        raise MissingSettingsError(plugin, var)

    return plugin_settings[var]


def import_plugins():
    scopes = get_active_settings().scopes

    for selected_plugins in scopes.values():
        for plugin_path in selected_plugins:
            import_plugin(plugin_path)


def set_plugin_setting(
    plugin: Type[AbstractPlugin], var: AbstractPluginSettingsVar, value: str
):
    try:
        plugin_settings = get_plugin_settings(plugin)
    except MissingSettingsError:
        plugin_settings = {}
        get_active_settings().settings[plugin.get_path()] = plugin_settings

    plugin_settings[var] = value

    save_settings(get_settings())


def delete_plugin_setting(plugin: Type[AbstractPlugin], var: AbstractPluginSettingsVar):
    try:
        plugin_settings = get_plugin_settings(plugin)
    except MissingSettingsError:
        return

    if var in plugin_settings:
        del plugin_settings[var]

    save_settings(get_settings())


def save_settings(settings: Settings):
    yaml_output = yaml.dump(settings, Dumper=EnumDumper)

    with open(get_settings_file_path(), "w") as f:
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


def _load_settings(file_path: str) -> Settings:
    """
    Loads the settings from the specified settings file, returning their raw string
    representations, or an empty dict if the file is not found.
    """
    loaded_settings: Dict[str, Any] = {}

    try:
        with open(file_path, "r") as f:
            loaded_yaml = yaml.load(f, yaml.Loader)

        if loaded_yaml is not None:
            loaded_settings = loaded_yaml
    except FileNotFoundError:
        logger.debug("Settings file %s not found", file_path)

    settings = Settings.make_default()

    settings.version = loaded_settings.get("version", CURRENT_SETTINGS_SCHEMA_VERSION)
    settings.profiles = loaded_settings.get("profiles", settings.profiles)

    # Normalizing settings to only have expected values and format as enum
    for profile_name, profile_settings in settings.profiles.items():
        if not isinstance(profile_settings, ProfileSettings):
            profile_settings = ProfileSettings(
                scopes=profile_settings.get("scopes", {}),
                settings=profile_settings.get("settings", {}),
            )
            settings.profiles[profile_name] = profile_settings

        _normalize_enum_keys(profile_settings.scopes, PluginScope)

        for plugin_path, plugin_settings in profile_settings.settings.items():
            plugin_settings_vars = _get_plugin_settings_vars(plugin_path)

            _normalize_enum_keys(plugin_settings, plugin_settings_vars)

    return settings


def _get_plugin_settings_vars(plugin_path: str) -> Type[AbstractPluginSettingsVar]:
    plugin_class = import_plugin(plugin_path)

    return plugin_class.get_settings_vars()


def _normalize_enum_keys(dict_, vars: Type[enum.Enum]):
    for key in list(dict_):
        normalized_key = _normalize_enum(vars, key)
        if normalized_key is None:
            logger.warning("Unknown key: %s", key)
        else:
            dict_[normalized_key] = dict_[key]

        del dict_[key]


EnumType = TypeVar("EnumType", bound=enum.Enum)


def _normalize_enum(enum_type: Type[EnumType], obj: Any) -> Optional[EnumType]:
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


def _apply_env_var_overrides(
    settings: PluginSettings, vars: Type[AbstractPluginSettingsVar]
) -> None:
    """
    Apply env var overrides on settings.
    """
    for var in vars:
        key = str(var.value)

        if key in os.environ:
            new_value = os.environ[key]
            logger.debug("Overriding %s from environment variable", key)

            settings[var] = new_value


def dump_settings(settings: ProfileSettings) -> str:
    """
    Dumps the specified settings to string.
    """
    return yaml.dump(settings, default_flow_style=False, Dumper=EnumDumper)


def _clear_cache():
    """
    Only for testing.
    """
    global _SETTINGS

    _SETTINGS = None
