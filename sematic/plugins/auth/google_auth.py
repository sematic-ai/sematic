# Standard Library
from http import HTTPStatus
from typing import Any, Dict

# Third-party
import flask
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests
from google.oauth2 import id_token
from sqlalchemy.orm.exc import NoResultFound

# Sematic
from sematic.abstract_plugin import AbstractPlugin
from sematic.api.app import sematic_api
from sematic.api.endpoints.request_parameters import jsonify_error
from sematic.config.server_settings import (
    ServerSettingsVar,
    get_plugin_settings,
    get_server_setting,
)
from sematic.config.settings import MissingPluginSettingsError
from sematic.db.models.factories import make_user
from sematic.db.queries import get_user, save_user
from sematic.plugins.abstract_auth import AbstractAuth

_OAUTH_CLIENT_ID_KEY = "GOOGLE_OAUTH_CLIENT_ID"
_LOGIN_ENDPOINT_ROUTE = "/login/google"


class GoogleAuth(AbstractAuth, AbstractPlugin):
    @staticmethod
    def get_author() -> str:
        return "github.com/sematic-ai"

    @classmethod
    def get_login_endpoint(cls) -> str:
        return _LOGIN_ENDPOINT_ROUTE

    @classmethod
    def get_slug(cls) -> str:
        return "google"

    @classmethod
    def get_public_auth_details(cls) -> Dict[str, Any]:
        return {
            _OAUTH_CLIENT_ID_KEY: cls.get_oauth_client_id(),
        }

    @classmethod
    def get_oauth_client_id(cls) -> str:
        plugins_settings = get_plugin_settings(cls.get_name())
        try:
            return plugins_settings[_OAUTH_CLIENT_ID_KEY]
        except KeyError:
            raise MissingPluginSettingsError(cls.get_name(), _OAUTH_CLIENT_ID_KEY)


@sematic_api.route(_LOGIN_ENDPOINT_ROUTE, methods=["POST"])
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
        google_oauth_client_id = GoogleAuth.get_oauth_client_id()
    except MissingPluginSettingsError:
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
            if idinfo.get("hd") != authorized_email_domain:
                raise ValueError("Incorrect email domain")

    except (ValueError, GoogleAuthError):
        return jsonify_error("Invalid user", HTTPStatus.UNAUTHORIZED)

    try:
        user = get_user(idinfo["email"])

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

    payload = {"user": user.to_json_encodable()}
    # API keys are redacted by default.
    # In this case we do need to pass it to the front-end.
    payload["user"]["api_key"] = user.api_key

    return flask.jsonify(payload)
