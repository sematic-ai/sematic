"""Metadata about the server itself."""

# Standard
# Standard Library
from typing import Optional

# Third-party
import flask

# Sematic
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate
from sematic.db.models.user import User
from sematic.user_settings import MissingSettingsError, SettingsVar, get_user_settings
from sematic.versions import CURRENT_VERSION, MIN_CLIENT_SERVER_SUPPORTS


@sematic_api.route("/api/v1/meta/versions", methods=["GET"])
def get_server_version_info() -> flask.Response:
    """Get information about the server version and clients it supports

    Returns
    -------
    A flask response with a json payload. The payload has two fields:
        server: the version of Sematic the server is running, as 3 integers. Note that
            clients whose version is greater than this may not work with the server.
        min_client_supported: the minimum version of Sematic the current server version
            supports. Clients with versions less than this may fail when used with the
            server.
    """
    payload = dict(
        server=CURRENT_VERSION,
        min_client_supported=MIN_CLIENT_SERVER_SUPPORTS,
    )

    return flask.jsonify(payload)


@sematic_api.route("/api/v1/meta/env", methods=["GET"])
@authenticate
def env_endpoint(user: Optional[User]) -> flask.Response:
    """Return a dictionary with information about the configuration of the server"""
    env = {}
    for settings in (
        SettingsVar.GOOGLE_OAUTH_CLIENT_ID,
        SettingsVar.KUBERNETES_NAMESPACE,
        SettingsVar.GRAFANA_PANEL_URL,
    ):
        try:
            env[settings.value] = get_user_settings(settings)
        except MissingSettingsError:
            continue

    return flask.jsonify(dict(env=env))
