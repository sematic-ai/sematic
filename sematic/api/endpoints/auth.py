# Standard library
import functools
from http import HTTPStatus
from typing import Callable

# Third-party
import flask
from google.oauth2 import id_token
from google.auth.transport import requests
from sqlalchemy.orm.exc import NoResultFound

# Sematic
from sematic.api.app import sematic_api
from sematic.api.endpoints.request_parameters import (
    jsonify_error,
)
from sematic.config import get_config
from sematic.db.models.factories import make_user
from sematic.db.queries import (
    get_user,
    get_user_by_api_key,
    save_user,
)


@sematic_api.route("/authenticate", methods=["GET"])
def authenticate_endpoint() -> flask.Response:
    """
    Tells the front-end whether or not to authenticate users.

    Ideally we would always authenticate but in order to keep a low discovery
    friction, we let users run locally without authentication.
    """
    return flask.jsonify({"authenticate": get_config().authenticate})


@sematic_api.route("/login/google", methods=["POST"])
def login() -> flask.Response:
    if not flask.request or not flask.request.json or "token" not in flask.request.json:
        return jsonify_error("Please provide a login token", HTTPStatus.BAD_REQUEST)

    token = flask.request.json["token"]
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            "977722105393-257kdkrc5dfbpu0jcsd8etn1k4u4q4ut.apps.googleusercontent.com",
        )
        if get_config().authorized_email_domain is not None:
            if idinfo["hd"] != get_config().authorized_email_domain:
                raise ValueError("Incorrect email domain")

    except Exception:
        return jsonify_error("Invalid user", HTTPStatus.UNAUTHORIZED)

    # Returned schema
    """
    {'iss': 'https://accounts.google.com',
    'nbf': int,
    'aud': '....apps.googleusercontent.com',
    'sub': '...',
    'hd': 'sematic.ai',
    'email': 'emmanuel@sematic.ai',
    'email_verified': True,
    'azp': '....apps.googleusercontent.com',
    'name': 'Emmanuel Turlay',
    'picture': 'https://...',
    'given_name': 'Emmanuel',
    'family_name': 'Turlay',
    'iat': ...,
    'exp': ...,
    'jti': '...'}
    """

    try:
        user = get_user(idinfo["email"])
    except NoResultFound:
        user = make_user(
            email=idinfo["email"],
            first_name=idinfo["given_name"],
            last_name=idinfo["family_name"],
            avatar_url=idinfo["picture"],
        )
        user = save_user(user)

    payload = {"user": user.to_json_encodable()}
    # API keys are redacted by default.
    # In this case we do need to pass it to the front-end.
    payload["user"]["api_key"] = user.api_key

    return flask.jsonify(payload)


def authenticate(endpoint_fn: Callable) -> Callable:
    """
    Decorator for endpoints who need authentication.
    """
    if not get_config().authenticate:

        @functools.wraps(endpoint_fn)
        def unauthenticated_endpoint(*args, **kwargs):
            return endpoint_fn(None, *args, **kwargs)

        return unauthenticated_endpoint

    @functools.wraps(endpoint_fn)
    def authenticated_endpoint(*args, **kwargs) -> flask.Response:
        request_api_key = flask.request.headers.get("X-API-KEY")
        if request_api_key is None:
            return jsonify_error("Missing API key", HTTPStatus.UNAUTHORIZED)

        try:
            user = get_user_by_api_key(request_api_key)
        except NoResultFound:
            return jsonify_error("Missing API key", HTTPStatus.UNAUTHORIZED)

        return endpoint_fn(user, *args, **kwargs)

    return authenticated_endpoint
