# Standard Library
import os
import shutil

# Sematic
from sematic.config.settings import (
    AbstractSettingsVar,
    MissingSettingsError,
    ProfileSettings,
    SettingsScope,
    as_bool,
)
from sematic.config.user_settings import get_user_settings_file_path


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


class ServerSettingsScope(SettingsScope):
    @property
    def settings_file_path(self) -> str:
        """
        Temporary override to enable smooth transition from one file
        to one file per scope.

        TODO: Remove this code.
        """
        expected_path = super().settings_file_path

        user_settings_file_path = get_user_settings_file_path()
        if not os.path.isfile(expected_path) and os.path.isfile(
            user_settings_file_path
        ):
            shutil.copy(user_settings_file_path, expected_path)

        return expected_path


_SERVER_SETTINGS_SCOPE = ServerSettingsScope(
    file_name="server.yaml",
    cli_command="server-settings",
    vars=ServerSettingsVar,
)


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


class MissingServerSettingsError(MissingSettingsError):
    def __init__(self, var: ServerSettingsVar):
        super().__init__(var, _SERVER_SETTINGS_SCOPE.cli_command)
