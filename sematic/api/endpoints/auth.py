# Standard Library
import functools
from http import HTTPStatus
from typing import Callable

# Third-party
import flask
from sqlalchemy.orm.exc import NoResultFound

# Sematic
from sematic.api.app import sematic_api
from sematic.api.endpoints.request_parameters import jsonify_error
from sematic.config.server_settings import ServerSettingsVar, get_bool_server_setting
from sematic.db.queries import get_user_by_api_key
from sematic.plugins.abstract_auth import get_auth_plugins
from sematic.plugins.auth.google_auth import GoogleAuth


@sematic_api.route("/authenticate", methods=["GET"])
def authenticate_endpoint() -> flask.Response:
    """
    Tells the front-end whether or not to authenticate users.

    Ideally we would always authenticate but in order to keep a low discovery
    friction, we let users run locally without authentication.
    """
    providers = {}
    authenticate = get_bool_server_setting(
        ServerSettingsVar.SEMATIC_AUTHENTICATE, False
    )

    if authenticate:
        selected_auth_plugins = get_auth_plugins([GoogleAuth])

        for auth_plugin in selected_auth_plugins:
            details = auth_plugin.get_public_auth_details()
            details["endpoint"] = auth_plugin.get_login_endpoint()

            providers[auth_plugin.get_slug()] = details

        if len(providers) == 0:
            return jsonify_error("No login providers", HTTPStatus.BAD_REQUEST)

    return flask.jsonify({"authenticate": authenticate, "providers": providers})


API_KEY_HEADER = "X-API-KEY"


def authenticate(endpoint_fn: Callable) -> Callable:
    """
    Decorator for endpoints who need authentication.
    """

    @functools.wraps(endpoint_fn)
    def endpoint(*args, **kwargs) -> flask.Response:
        authenticate = get_bool_server_setting(
            ServerSettingsVar.SEMATIC_AUTHENTICATE, False
        )
        if not authenticate:
            return endpoint_fn(None, *args, **kwargs)

        request_api_key = flask.request.headers.get(API_KEY_HEADER)
        if request_api_key is None:
            return jsonify_error("Missing API key", HTTPStatus.UNAUTHORIZED)

        try:
            user = get_user_by_api_key(request_api_key)
        except NoResultFound:
            return jsonify_error("Missing API key", HTTPStatus.UNAUTHORIZED)

        return endpoint_fn(user, *args, **kwargs)

    return endpoint
