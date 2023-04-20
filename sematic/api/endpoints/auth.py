# Standard Library
import functools
from http import HTTPStatus
from typing import Callable

# Third-party
import flask
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests
from google.oauth2 import id_token
from sqlalchemy.orm.exc import NoResultFound

# Sematic
from sematic.api.app import sematic_api
from sematic.api.endpoints.request_parameters import jsonify_error
from sematic.config.server_settings import (
    ServerSettingsVar,
    get_bool_server_setting,
    get_server_setting,
)
from sematic.config.settings import MissingSettingsError
from sematic.db.models.factories import make_user
from sematic.db.queries import get_user_by_api_key, get_user_by_email, save_user

# Email address for pseudo-user for the cron job that periodically
# makes requests to the API to clean up dangling resources.
CLEANER_EMAIL_ADDRESS = "cleaner@serviceaccount"


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
        for var in (
            ServerSettingsVar.GOOGLE_OAUTH_CLIENT_ID,
            # TODO: Github needs more work, npm package is broken
            # ServerSettingsVar.GITHUB_OAUTH_CLIENT_ID,
        ):
            try:
                providers[var.value] = get_server_setting(var)
            except MissingSettingsError:
                continue

        if len(providers) == 0:
            return jsonify_error("No login providers", HTTPStatus.BAD_REQUEST)

    return flask.jsonify({"authenticate": authenticate, "providers": providers})


@sematic_api.route("/login/google", methods=["POST"])
def google_login() -> flask.Response:
    """
    Google login.

    Schema returned by verify_oauth2_token:
    {'iss': 'https://accounts.google.com',
    'nbf': int,
    'aud': '....apps.googleusercontent.com',
    'sub': '...',
    'hd': 'example.com',
    'email': 'ringo@example.com',
    'email_verified': True,
    'azp': '....apps.googleusercontent.com',
    'name': 'Ringo Starr',
    'picture': 'https://...',
    'given_name': 'Ringo',
    'family_name': 'Starr',
    'iat': ...,
    'exp': ...,
    'jti': '...'}
    """
    if not flask.request or not flask.request.json or "token" not in flask.request.json:
        return jsonify_error("Please provide a login token", HTTPStatus.BAD_REQUEST)

    token = flask.request.json["token"]

    try:
        google_oauth_client_id = get_server_setting(
            ServerSettingsVar.GOOGLE_OAUTH_CLIENT_ID
        )
    except MissingSettingsError:
        return jsonify_error("Missing oauth client ID", HTTPStatus.BAD_REQUEST)

    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            google_oauth_client_id,
        )

        authorized_email_domain = get_server_setting(
            ServerSettingsVar.SEMATIC_AUTHORIZED_EMAIL_DOMAIN, None
        )

        if authorized_email_domain is not None:
            if idinfo.get("hd") not in authorized_email_domain.split(","):
                raise ValueError("Incorrect email domain")

    except (ValueError, GoogleAuthError):
        return jsonify_error("Invalid user", HTTPStatus.UNAUTHORIZED)

    try:
        user = get_user_by_email(idinfo["email"])

        # In case these have changed
        user.first_name = idinfo["given_name"]
        user.last_name = idinfo["family_name"]
        user.avatar_url = idinfo["picture"]
    except NoResultFound:
        user = make_user(
            email=idinfo["email"],
            first_name=idinfo["given_name"],
            last_name=idinfo["family_name"],
            avatar_url=idinfo["picture"],
        )

    user = save_user(user)

    # API keys are redacted by default.
    # In this case we do need to pass it to the front-end.
    payload = {"user": user.to_json_encodable(redact=False)}

    return flask.jsonify(payload)


def get_cleaner_api_key() -> str:
    """Get an API key for the cleaner, or make one if it doesn't exist.

    This should NEVER be exposed via an endpoint. Running it requires
    DB access, which ensures that it can only be done by sufficiently
    privileged code.

    Returns
    -------
    An API key that can be used to authenticate as the user for the cleaner.
    """
    try:
        user = get_user_by_email(CLEANER_EMAIL_ADDRESS)
    except NoResultFound:
        user = make_user(
            email=CLEANER_EMAIL_ADDRESS,
            first_name=None,
            last_name=None,
            avatar_url=None,
        )
        save_user(user)
    return user.api_key


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
