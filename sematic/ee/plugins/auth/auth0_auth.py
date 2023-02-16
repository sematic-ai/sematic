# Standard Library
from http import HTTPStatus
from typing import Any, Dict, Type

# Third-party
import flask
from auth0.authentication import Social  # type: ignore

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


class Auth0AuthSettingsVar(AbstractPluginSettingsVar):
    AUTH0_CLIENT_ID = "AUTH0_CLIENT_ID"
    AUTH0_TENANT_DOMAIN = "AUTH0_TENANT_DOMAIN"
    SOCIAL_CONNECTION = "SOCIAL_CONNECTION"


_LOGIN_ENDPOINT_ROUTE = "/login/auth0"


class Auth0Auth(AbstractAuth, AbstractPlugin):
    """
    Auth0 authentication plugin.
    """

    @staticmethod
    def get_author() -> str:
        return SEMATIC_PLUGIN_AUTHOR

    @staticmethod
    def get_version() -> PluginVersion:
        return (0, 1, 0)

    @classmethod
    def get_settings_vars(cls) -> Type[AbstractPluginSettingsVar]:
        return Auth0AuthSettingsVar

    @classmethod
    def get_login_endpoint(cls) -> str:
        return _LOGIN_ENDPOINT_ROUTE

    @classmethod
    def get_slug(cls) -> str:
        return "auth0"

    @classmethod
    def get_public_auth_details(cls) -> Dict[str, Any]:
        return {
            var.value: get_plugin_setting(cls, var)
            for var in (
                Auth0AuthSettingsVar.AUTH0_CLIENT_ID,
                Auth0AuthSettingsVar.AUTH0_TENANT_DOMAIN,
            )
        }


@sematic_api.route(_LOGIN_ENDPOINT_ROUTE, methods=["POST"])
def auth0_login() -> flask.Response:
    """
    Sample ID token
    {
        "iss": "http://my-domain.auth0.com",
        "sub": "auth0|123456",
        "aud": "my_client_id",
        "exp": 1311281970,
        "iat": 1311280970,
        "name": "Jane Doe",
        "given_name": "Jane",
        "family_name": "Doe",
        "gender": "female",
        "birthdate": "0000-10-31",
        "email": "janedoe@example.com",
        "picture": "http://example.com/janedoe/me.jpg"
    }
    """
    if not flask.request or not flask.request.json or "token" not in flask.request.json:
        return jsonify_error("Please provide a login token", HTTPStatus.BAD_REQUEST)

    token = flask.request.json["token"]

    try:
        client_id = get_plugin_setting(Auth0Auth, Auth0AuthSettingsVar.AUTH0_CLIENT_ID)
        tenant_domain = get_plugin_setting(
            Auth0Auth, Auth0AuthSettingsVar.AUTH0_TENANT_DOMAIN
        )
        social_connection = get_plugin_setting(
            Auth0Auth, Auth0AuthSettingsVar.SOCIAL_CONNECTION, "google"
        )
    except MissingSettingsError:
        return jsonify_error(
            "Missing Auth0 client ID or tenant domain", HTTPStatus.BAD_REQUEST
        )

    auth0_client = Social(tenant_domain, client_id)

    response = auth0_client.login(token, social_connection)

    if "access_token" not in response or "id_token" not in response:
        return jsonify_error("Invalid user", HTTPStatus.UNAUTHORIZED)

    oidc_user = OIDCUser(**response["id_token"])
    email_domail = oidc_user.email.split("@")[1]

    if not is_email_domain_authorized(email_domail):
        return jsonify_error("Invalid user", HTTPStatus.UNAUTHORIZED)

    user = get_user_from_oidc(oidc_user)

    payload = {"user": user.to_json_encodable()}

    # API keys are redacted by default.
    # In this case we do need to pass it to the front-end.
    payload["user"]["api_key"] = user.api_key

    return flask.jsonify(payload)
