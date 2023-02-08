# Standard Library
import distutils.util
import enum
import logging
import os
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Literal, Optional, Type, TypeVar, Union, cast

# Third-party
import yaml

# Sematic
from sematic.abstract_plugin import (
    AbstractPlugin,
    AbstractPluginSettingsVar,
    MissingPluginError,
    PluginScope,
    import_plugin,
)
from sematic.config.config_dir import get_config_dir
from sematic.versions import SETTINGS_SCHEMA_VERSION

logger = logging.getLogger(__name__)


_DEFAULT_PROFILE = "default"
_SETTINGS_FILE_NAME = "settings.yaml"
_PLUGIN_VERSION_KEY: Literal["__version__"] = "__version__"

PluginScopes = Dict[PluginScope, List[str]]
PluginSettings = Dict[Union[AbstractPluginSettingsVar, Literal["__version__"]], str]
PluginsSettings = Dict[str, PluginSettings]

# providing textual path instead of importing in order to avoid a dependency cycle
# these plugins are "known" and will always be part of the server deployment
_MANDATORY_SYSTEM_PLUGIN_PATHS = [
    "sematic.config.server_settings.ServerSettings",
    "sematic.config.user_settings.UserSettings",
]


@dataclass
class ProfileSettings:
    """
    Settings for one profile.
    """

    scopes: PluginScopes = field(default_factory=dict)
    settings: PluginsSettings = field(default_factory=dict)


@dataclass
class Settings:
    """
    Represents the entire content of the settings file.
    """

    version: int = field(default_factory=lambda: SETTINGS_SCHEMA_VERSION)
    profiles: Dict[str, ProfileSettings] = field(
        default_factory=lambda: {_DEFAULT_PROFILE: ProfileSettings()}
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
_ACTIVE_SETTINGS: Optional[ProfileSettings] = None


def get_settings_file_path() -> str:
    """
    Get full patch to settings file.
    """
    return os.path.join(get_config_dir(), _SETTINGS_FILE_NAME)


def get_settings() -> Settings:
    """
    Get entire cached settings file payload, no CLI override.
    """
    global _SETTINGS

    if _SETTINGS is None:
        _SETTINGS = _load_settings(get_settings_file_path())

    return _SETTINGS


def get_active_settings() -> ProfileSettings:
    """
    Gets cached currently active settings.

    Gets the default profile settings and applies CLI overrides.
    """
    global _ACTIVE_SETTINGS

    if _ACTIVE_SETTINGS is None:
        settings = get_settings()

        profile_settings = settings.profiles[_DEFAULT_PROFILE]

        _apply_scopes_overrides(profile_settings.scopes)
        _ensure_mandatory_plugins(profile_settings.settings)

        for plugin_path, plugin_settings in profile_settings.settings.items():
            plugin_settings_vars = _get_plugin_settings_vars(plugin_path)
            _apply_env_var_overrides(plugin_settings, plugin_settings_vars)

        _ACTIVE_SETTINGS = profile_settings

    return _ACTIVE_SETTINGS


T = TypeVar("T", bound=Type[AbstractPlugin])


def get_plugins_with_interface(
    interface: T, scope: PluginScope, default: List[Type[AbstractPlugin]]
) -> List[T]:
    """Gets active plugins for a scope, but only ones implementing a given interface."""
    for plugin in default:
        if not issubclass(plugin, interface):
            raise ValueError(f"{plugin} is not a subclass of {interface}")
    plugins = get_active_plugins(scope, default=[])
    plugins = [
        plugin for plugin in plugins if issubclass(plugin, interface)  # type: ignore
    ]
    if len(plugins) == 0:
        return cast(List[T], default)
    return cast(List[T], plugins)


def get_active_plugins(
    scope: PluginScope, default: List[Type[AbstractPlugin]]
) -> List[Type[AbstractPlugin]]:
    """
    Gets the active plugins for scope.
    """
    scopes = get_active_settings().scopes

    if scope not in scopes:
        return default

    imported_plugins = [import_plugin(plugin_path) for plugin_path in scopes[scope]]

    return imported_plugins


def get_plugin_settings(
    plugin: Type[AbstractPlugin],
) -> PluginSettings:
    """
    Gets active settings for plugin.
    """
    settings = get_active_settings().settings

    plugin_path = plugin.get_path()

    if plugin_path not in settings:
        raise MissingSettingsError(plugin)

    return {
        key: value
        for key, value in settings[plugin_path].items()
        if key != _PLUGIN_VERSION_KEY
    }


def get_plugin_setting(
    plugin: Type[AbstractPlugin], var: AbstractPluginSettingsVar, *args
) -> str:
    """
    Gets var setting value for plugin.
    """
    try:
        plugin_settings = get_plugin_settings(plugin)
    except MissingSettingsError:
        plugin_settings = {}

    if var not in plugin_settings:
        # _apply_env_var_overrides only applies overrides
        # to settings present in the settings file
        # This ensures env var overrides are still applied
        # if the setting was not set in the file
        if var.value in os.environ:
            return os.environ[var.value]

        if len(args) > 0:
            return args[0]

        raise MissingSettingsError(plugin, var)

    return plugin_settings[var]


def import_plugins() -> None:
    """
    Imports all configured plugins.
    """
    scopes = get_active_settings().scopes

    for selected_plugins in scopes.values():
        for plugin_path in selected_plugins:
            import_plugin(plugin_path)


def set_plugin_setting(
    plugin: Type[AbstractPlugin], var: AbstractPluginSettingsVar, value: str
) -> None:
    """
    Sets a plug-in setting value.
    """
    try:
        plugin_settings = get_plugin_settings(plugin)
    except MissingSettingsError:
        plugin_settings = {}

    if _normalize_enum(plugin.get_settings_vars(), var) is None:
        raise ValueError(
            f"Unknown setting for plug-in {plugin.get_path()}: {var.value}"
        )

    plugin_settings[var] = value
    plugin_settings[_PLUGIN_VERSION_KEY] = ".".join(
        str(v) for v in plugin.get_version()
    )

    get_active_settings().settings[plugin.get_path()] = plugin_settings

    save_settings(get_settings())


def delete_plugin_setting(
    plugin: Type[AbstractPlugin], var: AbstractPluginSettingsVar
) -> None:
    """
    Deletes a plug-in setting value.
    """
    try:
        plugin_settings = get_plugin_settings(plugin)
    except MissingSettingsError:
        logger.warning("%s has no saved settings", plugin.get_path())
        return

    if var in plugin_settings:
        del plugin_settings[var]

    get_active_settings().settings[plugin.get_path()] = plugin_settings

    save_settings(get_settings())


def save_settings(settings: Settings) -> None:
    """
    Persists settings to file.
    """
    yaml_output = yaml.dump(asdict(settings), Dumper=EnumDumper)

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

    settings = Settings()

    settings.version = loaded_settings.get("version", SETTINGS_SCHEMA_VERSION)
    settings.profiles = loaded_settings.get("profiles", settings.profiles)

    # Normalizing settings to only have expected values and format as enum
    for profile_name, profile_settings in settings.profiles.items():
        if not isinstance(profile_settings, ProfileSettings):
            profile_settings = ProfileSettings(
                scopes=profile_settings.get("scopes") or {},
                settings=profile_settings.get("settings") or {},
            )
            settings.profiles[profile_name] = profile_settings

        profile_settings.scopes = _normalize_enum_keys(
            profile_settings.scopes, PluginScope
        )

        # We are mutating the dictionary as we iterate, so we iterate on keys.
        for plugin_path in list(profile_settings.settings):
            try:
                plugin = import_plugin(plugin_path)
            except MissingPluginError as e:
                # It's important to not fail when plug-ins cannot be found as users
                # may exchange settings files for different installs
                logger.warning(str(e))
                del profile_settings.settings[plugin_path]
                continue

            plugin_settings_vars = _get_plugin_settings_vars(plugin_path)

            plugin_settings = profile_settings.settings[plugin_path]

            plugin_settings_version = plugin_settings.get(_PLUGIN_VERSION_KEY)
            if plugin_settings_version is not None:
                major_plugin_version = plugin.get_version()[0]
                if int(plugin_settings_version.split(".")[0]) < major_plugin_version:
                    logger.warning(
                        (
                            "Settings for plug-in %s "
                            "have lower major version number (%s) "
                            "than the plug-in (%s)"
                        ),
                        plugin_path,
                        plugin_settings_version,
                        major_plugin_version,
                    )

            profile_settings.settings[plugin_path] = _normalize_enum_keys(
                plugin_settings, plugin_settings_vars
            )

    return settings


def _get_plugin_settings_vars(plugin_path: str) -> Type[AbstractPluginSettingsVar]:
    plugin_class = import_plugin(plugin_path)

    return plugin_class.get_settings_vars()


EnumType = TypeVar("EnumType", bound=enum.Enum)


def _normalize_enum_keys(
    dict_: Dict[Union[str, EnumType], Any], vars: Type[EnumType]
) -> Dict[Union[EnumType, Literal["__version__"]], Any]:
    normalized_dict: Dict[Union[EnumType, Literal["__version__"]], Any] = {}

    for key in list(dict_):
        normalized_key = (
            key if key == _PLUGIN_VERSION_KEY else _normalize_enum(vars, key)
        )

        if normalized_key is None:
            logger.warning("Unknown key: %s", key)
        else:
            normalized_dict[normalized_key] = dict_[key]

    return normalized_dict


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


def _apply_scopes_overrides(plugin_scopes: PluginScopes) -> None:
    """
    Adds system plugins that are declared in env variables, but not in the settings file.
    """
    for scope in PluginScope:
        if scope.value in os.environ:
            logger.debug("Overriding scope %s from environment variables", scope.value)

            plugin_scopes[scope] = [
                plugin_path.strip()
                for plugin_path in os.environ[scope.value].split(",")
                if plugin_path.strip() != ""
            ]


def _ensure_mandatory_plugins(plugin_settings: PluginsSettings) -> None:
    """
    Adds the mandatory system plugins to the parameter, if not present.
    """
    for plugin_path in _MANDATORY_SYSTEM_PLUGIN_PATHS:
        if plugin_path not in plugin_settings:
            plugin_settings[plugin_path] = {}


def dump_settings(settings: ProfileSettings) -> str:
    """
    Dumps the specified settings to string.
    """
    return yaml.dump(asdict(settings), default_flow_style=False, Dumper=EnumDumper)
