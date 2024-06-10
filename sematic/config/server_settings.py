# Standard Library
import functools
import json
from typing import Dict, Tuple, Type, cast

# Sematic
from sematic.abstract_plugin import (
    SEMATIC_PLUGIN_AUTHOR,
    AbstractPlugin,
    AbstractPluginSettingsVar,
)
from sematic.config.settings import (
    MissingSettingsError,
    delete_plugin_setting,
    get_plugin_setting,
    get_plugin_settings,
    set_plugin_setting,
)
from sematic.utils.types import as_bool


class ServerSettingsVar(AbstractPluginSettingsVar):
    # Sematic
    SEMATIC_AUTHENTICATE = "SEMATIC_AUTHENTICATE"
    SEMATIC_AUTHORIZED_EMAIL_DOMAIN = "SEMATIC_AUTHORIZED_EMAIL_DOMAIN"
    SEMATIC_WORKER_API_ADDRESS = "SEMATIC_WORKER_API_ADDRESS"
    SEMATIC_DASHBOARD_URL = "SEMATIC_DASHBOARD_URL"
    SEMATIC_WORKER_SOCKET_IO_ADDRESS = "SEMATIC_WORKER_SOCKET_IO_ADDRESS"
    SEMATIC_WSGI_WORKERS_COUNT = "SEMATIC_WSGI_WORKERS_COUNT"

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

    # Controls which Kubernetes annotations pipeline authors
    # can apply to their jobs.
    SEMATIC_WORKER_ALLOWED_ANNOTATION_KEYS = "SEMATIC_WORKER_ALLOWED_ANNOTATION_KEYS"

    # Controls which Kubernetes labels pipeline authors
    # can apply to their jobs.
    SEMATIC_WORKER_ALLOWED_LABEL_KEYS = "SEMATIC_WORKER_ALLOWED_LABEL_KEYS"

    # What, if any, imagePullSecrets should be used for runner and
    # standalone jobs?
    WORKER_IMAGE_PULL_SECRETS = "WORKER_IMAGE_PULL_SECRETS"

    # Controls whether users who are defining pipelines can
    # customize the Kubernetes security context in which their
    # job runs.
    ALLOW_CUSTOM_SECURITY_CONTEXTS = "ALLOW_CUSTOM_SECURITY_CONTEXTS"

    # Controls whether users can mount underlying Kubernetes node
    # paths into the Worker pods.
    ALLOW_HOST_PATH_MOUNTING = "ALLOW_HOST_PATH_MOUNTING"

    # GRAFANA
    GRAFANA_PANEL_URL = "GRAFANA_PANEL_URL"


class ServerSettings(AbstractPlugin):
    @staticmethod
    def get_author() -> str:
        return SEMATIC_PLUGIN_AUTHOR

    @staticmethod
    def get_version() -> Tuple[int, int, int]:
        return 0, 1, 0

    @classmethod
    def get_settings_vars(cls) -> Type[AbstractPluginSettingsVar]:
        return ServerSettingsVar


def get_active_server_settings() -> Dict[ServerSettingsVar, str]:
    try:
        server_settings = get_plugin_settings(ServerSettings)
    except MissingSettingsError:
        server_settings = {}

    return cast(Dict[ServerSettingsVar, str], server_settings)


get_server_setting = functools.partial(get_plugin_setting, ServerSettings)
set_server_setting = functools.partial(set_plugin_setting, ServerSettings)
delete_server_setting = functools.partial(delete_plugin_setting, ServerSettings)


def get_bool_server_setting(var: ServerSettingsVar, *args) -> bool:
    """
    Retrieves and returns the specified settings value as a boolean, with environment
    override.

    Loads and returns the specified settings value. If it does not exist, it falls back
    on the first optional vararg as a default value. If that does not exist, it raises.
    """
    return as_bool(get_server_setting(var, *args))


def get_json_server_setting(var: ServerSettingsVar, *args):
    """
    Retrieves and returns the specified settings value as a json-encodable, with
    environment override.

    Loads and returns the specified settings value. If it does not exist, it falls back
    on the first optional vararg as a default value. If that does not exist, it raises.
    """
    as_str = get_server_setting(var, *[json.dumps(arg) for arg in args])
    return json.loads(as_str)
