# Standard Library
from http import HTTPStatus
from typing import Any, Dict, Type

# Third-party
import flask
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests
from google.oauth2 import id_token

# Sematic
from sematic.abstract_plugin import (
    SEMATIC_PLUGIN_AUTHOR,
    AbstractPlugin,
    AbstractPluginSettingsVar,
    PluginVersion,
)
from sematic.api.app import sematic_api
from sematic.api.endpoints.request_parameters import jsonify_error
from sematic.config.settings import MissingSettingsError, get_plugin_setting
from sematic.plugins.abstract_auth import (
    AbstractAuth,
    OIDCUser,
    get_user_from_oidc,
    is_email_domain_authorized,
)


class GoogleAuthSettingsVar(AbstractPluginSettingsVar):
    GOOGLE_OAUTH_CLIENT_ID = "GOOGLE_OAUTH_CLIENT_ID"


_LOGIN_ENDPOINT_ROUTE = "/login/google"


class GoogleAuth(AbstractAuth, AbstractPlugin):
    @staticmethod
    def get_author() -> str:
        return SEMATIC_PLUGIN_AUTHOR

    @staticmethod
    def get_version() -> PluginVersion:
        return (0, 1, 0)

    @classmethod
    def get_settings_vars(cls) -> Type[AbstractPluginSettingsVar]:
        return GoogleAuthSettingsVar

    @classmethod
    def get_login_endpoint(cls) -> str:
        return _LOGIN_ENDPOINT_ROUTE

    @classmethod
    def get_slug(cls) -> str:
        return "google"

    @classmethod
    def get_public_auth_details(cls) -> Dict[str, Any]:
        return {
            GoogleAuthSettingsVar.GOOGLE_OAUTH_CLIENT_ID.value: cls.get_oauth_client_id(),
        }

    @classmethod
    def get_oauth_client_id(cls) -> str:
        return get_plugin_setting(cls, GoogleAuthSettingsVar.GOOGLE_OAUTH_CLIENT_ID)


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
    except MissingSettingsError:
        return jsonify_error("Missing oauth client ID", HTTPStatus.BAD_REQUEST)

    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            google_oauth_client_id,
        )

        if not is_email_domain_authorized(idinfo.get("hd")):
            raise ValueError("Incorrect email domain")

    except (ValueError, GoogleAuthError):
        return jsonify_error("Invalid user", HTTPStatus.UNAUTHORIZED)

    user = get_user_from_oidc(OIDCUser(**idinfo))

    payload = {"user": user.to_json_encodable()}

    # API keys are redacted by default.
    # In this case we do need to pass it to the front-end.
    payload["user"]["api_key"] = user.api_key

    return flask.jsonify(payload)
