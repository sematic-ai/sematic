# Standard Library
from typing import Any, Dict, List, Type, cast

# Sematic
from sematic.abstract_plugin import AbstractPlugin, PluginScope, import_plugin
from sematic.config.settings import (
    PLUGINS_SCOPES_KEY,
    PLUGINS_SETTINGS_KEY,
    AbstractSettingsVar,
    PluginsSettings,
    ProfileSettings,
    SettingsScope,
    as_bool,
)


class ServerSettingsVar(AbstractSettingsVar):
    # Sematic
    SEMATIC_AUTHENTICATE = "SEMATIC_AUTHENTICATE"
    SEMATIC_AUTHORIZED_EMAIL_DOMAIN = "SEMATIC_AUTHORIZED_EMAIL_DOMAIN"
    SEMATIC_WORKER_API_ADDRESS = "SEMATIC_WORKER_API_ADDRESS"

    # Google
    GOOGLE_OAUTH_CLIENT_ID = "GOOGLE_OAUTH_CLIENT_ID"

    # Github
    GITHUB_OAUTH_CLIENT_ID = "GITHUB_OAUTH_CLIENT_ID"

    # Kubernetes

    # Controls the Kubernetes namespace that the server will launch
    # jobs into
    KUBERNETES_NAMESPACE = "KUBERNETES_NAMESPACE"

    # Controls which Kubernetes Service Account the server
    # uses for jobs.
    SEMATIC_WORKER_KUBERNETES_SA = "SEMATIC_WORKER_KUBERNETES_SA"

    # GRAFANA
    GRAFANA_PANEL_URL = "GRAFANA_PANEL_URL"

    PLUGINS = "plugins"


_SERVER_SETTINGS_SCOPE = SettingsScope(
    file_name="server.yaml",
    cli_command="server-settings",
    vars=ServerSettingsVar,
)


def get_server_settings_scope() -> SettingsScope:
    return _SERVER_SETTINGS_SCOPE


def get_active_server_settings() -> ProfileSettings:
    return _SERVER_SETTINGS_SCOPE.get_active_settings()


def get_server_setting(var: ServerSettingsVar, *args) -> str:
    """
    Retrieves and returns the specified settings value, with environment override.

    Loads and returns the specified settings value. If it does not exist, it falls back
    on the first optional vararg as a default value. If that does not exist, it raises.
    """
    return _SERVER_SETTINGS_SCOPE.get_setting(var, *args)


def get_bool_server_setting(var: ServerSettingsVar, *args) -> bool:
    """
    Retrieves and returns the specified settings value as a boolean, with environment
    override.

    Loads and returns the specified settings value. If it does not exist, it falls back
    on the first optional vararg as a default value. If that does not exist, it raises.
    """
    return as_bool(get_server_setting(var, *args))


def set_server_settings(var: ServerSettingsVar, value: str) -> None:
    """
    Sets the specifies settings value and persists the settings.
    """
    _SERVER_SETTINGS_SCOPE.set_setting(var, value)


def delete_server_settings(var: ServerSettingsVar) -> None:
    """
    Deletes the specified settings value and persists the settings.
    """
    _SERVER_SETTINGS_SCOPE.delete_setting(var)


def get_selected_plugins(
    scope: PluginScope, default: List[Type[AbstractPlugin]]
) -> List[Type[AbstractPlugin]]:
    active_settings = get_active_server_settings()

    plugins_settings = cast(
        PluginsSettings,
        active_settings.get(ServerSettingsVar.PLUGINS, {PLUGINS_SCOPES_KEY: {}}),
    )

    plugin_paths: List[str] = plugins_settings.get(PLUGINS_SCOPES_KEY, {}).get(
        scope.value, []
    )

    if len(plugin_paths) == 0:
        return default

    return [import_plugin(plugin_path) for plugin_path in plugin_paths]


def get_plugin_settings(plugin_name: str) -> Dict[str, Any]:
    plugin_settings = _SERVER_SETTINGS_SCOPE.get_plugin_settings(
        ServerSettingsVar.PLUGINS
    )

    return plugin_settings[PLUGINS_SETTINGS_KEY].get(plugin_name, [])


def import_server_plugins() -> None:
    _SERVER_SETTINGS_SCOPE.import_plugins(ServerSettingsVar.PLUGINS)
