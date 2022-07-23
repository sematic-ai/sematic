# Standard library
from http import HTTPStatus

# Third-party
import flask
from google.oauth2 import id_token  # type: ignore
from google.auth.transport import requests  # type: ignore

# Sematic
from sematic.api.app import sematic_api
from sematic.api.endpoints.request_parameters import (
    jsonify_error,
)
from sematic.config import get_config


@sematic_api.route("/authenticate", methods=["GET"])
def authenticate() -> flask.Response:
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
        return jsonify_error("Invalid user", HTTPStatus.FORBIDDEN)

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

    payload = {
        "email": idinfo["email"],
        "first_name": idinfo["given_name"],
        "last_name": idinfo["family_name"],
        "picture": idinfo["picture"],
    }

    return flask.jsonify(payload)
