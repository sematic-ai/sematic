"""Metadata about the server itself."""

# Standard Library
from typing import Optional

# Third-party
import flask

# Sematic
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate
from sematic.config.server_settings import ServerSettingsVar, get_server_setting
from sematic.config.settings import MissingSettingsError
from sematic.db.models.user import User
from sematic.versions import CURRENT_VERSION, MIN_CLIENT_SERVER_SUPPORTS


@sematic_api.route("/api/v1/meta/versions", methods=["GET"])
def get_server_version_info() -> flask.Response:
    """Get information about the server version and clients it supports.

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
    """Return a dictionary with information about the configuration of the server."""
    env = {}
    for settings in (
        ServerSettingsVar.GOOGLE_OAUTH_CLIENT_ID,
        ServerSettingsVar.GRAFANA_PANEL_URL,
    ):
        try:
            env[settings.value] = get_server_setting(settings)
        except MissingSettingsError:
            continue

    return flask.jsonify(dict(env=env))
