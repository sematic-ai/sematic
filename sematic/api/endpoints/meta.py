"""Metadata about the server itself."""

# Standard Library
from logging import getLogger
from typing import Optional

# Third-party
import flask
import sqlalchemy

# Sematic
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate
from sematic.config.server_settings import ServerSettingsVar, get_server_setting
from sematic.config.settings import MissingSettingsError
from sematic.db.db import db
from sematic.db.models.user import User
from sematic.versions import CURRENT_VERSION, MIN_CLIENT_SERVER_SUPPORTS


logger = getLogger(__name__)


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


@sematic_api.route("/api/v1/meta/health", methods=["GET"])
def get_server_health() -> flask.Response:
    """Get information about the server health.

    Returns
    -------
    A flask response with a json payload. The payload has two fields:
        api: status info about basic access to the API
        db: status info about access to the DB
    Status info for each of these fields is a dict of the form:
    {
        "healthy": <bool>,
        "message": <str message about status>,
    }
    """
    # healthy by nature of the fact that this API is working.
    api_status = dict(
        healthy=True,
        message="API is healthy",
    )

    db_healthy = True
    db_message = "Basic database access verified"
    with db().get_session() as session:
        try:
            statement = sqlalchemy.text("SELECT id FROM runs LIMIT 1;")
            if len(list(session.execute(statement))) > 0:
                db_message = "Verified at least one run is present in the DB."

        except Exception as e:
            logger.fatal(
                "Sematic is unable to access the database and "
                "therefore will be unable to operate properly: %s",
                e,
            )
            db_healthy = False
            db_message = f"Problems accessing the database. Error: {e}"

    db_status = dict(
        healthy=db_healthy,
        message=db_message,
    )
    payload = dict(
        api=api_status,
        db=db_status,
    )

    response = flask.jsonify(payload)
    return response
