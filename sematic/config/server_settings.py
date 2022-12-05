# Standard Library
import enum
import logging
import os
from typing import Dict, Optional

# Sematic
from sematic.config.config_dir import SERVER_SETTINGS_FILE, get_config_dir
from sematic.config.settings import (
    _as_bool,
    _load_settings,
    _normalize_enum,
    _save_settings,
)

logger = logging.getLogger(__name__)


class ServerSettingsVar(enum.Enum):
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


class MissingServerSettingsError(Exception):
    def __init__(self, missing_settings: ServerSettingsVar):
        # TODO #264: this bleeds cli implementations details
        # this message should be set when triaging all exceptions before being surfaced
        # to the user
        message = """
Missing settings: {}

Set it with:

    $ sematic server-settings set {} VALUE
""".format(
            missing_settings.value, missing_settings.value
        )
        super().__init__(message)


ServerSettings = Dict[ServerSettingsVar, str]
# global settings cache
_settings: Optional[ServerSettings] = None


def _get_default_server_settings() -> ServerSettings:
    """
    Returns modifiable default settings.
    """
    return {}


def _get_server_settings_file() -> str:
    """
    Returns the path to the server settings file according to the configuration.
    """
    return os.path.join(get_config_dir(), SERVER_SETTINGS_FILE)


def _load_server_settings() -> ServerSettings:
    """
    Loads the settings from the configured settings file.
    """
    raw_settings = _load_settings(_get_server_settings_file())

    if raw_settings is None:
        return _get_default_server_settings()

    server_settings = {}

    for var, value in raw_settings.items():
        normalized_var = _normalize_enum(ServerSettingsVar, var)

        if normalized_var is None:
            raise ValueError(f"Unknown server setting {var}!")

        server_settings[normalized_var] = str(value)

    return server_settings


def _save_server_settings(settings: ServerSettings) -> None:
    """
    Persists the specified settings to the configured settings file.
    """
    _save_settings(_get_server_settings_file(), settings)


def get_active_server_settings() -> ServerSettings:
    """
    Returns all the active user settings, with environment overrides.
    """
    global _settings

    if _settings is None:
        _settings = _load_server_settings()

        # Override with env vars
        for var in ServerSettingsVar:
            key = str(var.value)
            if key in os.environ:
                new_value = os.environ[key]
                logger.debug("Overriding %s with %s", key, new_value)
                _settings[var] = new_value

    return _settings


def get_server_settings(var: ServerSettingsVar, *args) -> str:
    """
    Retrieves and returns the specified settings value, with environment override.

    Loads and returns the specified settings value. If it does not exist, it falls back
    on the first optional vararg as a default value. If that does not exist, it raises.
    """
    value = get_active_server_settings().get(var)

    if value is not None:
        return str(value)

    if len(args) >= 1:
        return args[0]

    raise MissingServerSettingsError(var)


def get_bool_server_settings(var: ServerSettingsVar, *args) -> bool:
    """
    Retrieves and returns the specified settings value as a boolean, with environment
    override.

    Loads and returns the specified settings value. If it does not exist, it falls back
    on the first optional vararg as a default value. If that does not exist, it raises.
    """
    return _as_bool(get_server_settings(var, *args))


def set_server_settings(var: ServerSettingsVar, value: str) -> None:
    """
    Sets the specifies settings value and persists the settings.
    """
    global _settings

    if _settings is None:
        _settings = _load_server_settings()

    _settings[var] = value
    _save_server_settings(_settings)


def delete_server_settings(var: ServerSettingsVar) -> None:
    """
    Deletes the specified settings value and persists the settings.
    """
    global _settings

    if _settings is None:
        _settings = _load_server_settings()

    if var not in _settings:
        raise ValueError(f"{var.value} is not present in the settings!")

    del _settings[var]
    _save_server_settings(_settings)
