# Standard Library
import uuid
from http import HTTPStatus
from typing import Dict
from unittest import mock

# Third-party
import flask
import flask.testing
import pytest
from google.auth.exceptions import GoogleAuthError

# Sematic
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate
from sematic.api.tests.fixtures import (  # noqa: F401
    mock_requests,
    mock_server_settings,
    test_client,
)
from sematic.config.server_settings import ServerSettingsVar
from sematic.config.settings import as_bool
from sematic.db.models.user import User
from sematic.db.queries import get_user
from sematic.db.tests.fixtures import persisted_user, test_db  # noqa: F401


@pytest.mark.parametrize(
    "authenticate_config, expected_providers",
    [
        ("false", {}),
        ("False", {}),
        ("0", {}),
        ("true", {"GOOGLE_OAUTH_CLIENT_ID": "ABC123"}),
        ("True", {"GOOGLE_OAUTH_CLIENT_ID": "ABC123"}),
        ("1", {"GOOGLE_OAUTH_CLIENT_ID": "ABC123"}),
    ],
)
def test_authenticate_endpoint(
    authenticate_config: str,
    expected_providers: Dict[str, str],
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    with mock_server_settings(
        {
            ServerSettingsVar.SEMATIC_AUTHENTICATE: authenticate_config,
            ServerSettingsVar.GOOGLE_OAUTH_CLIENT_ID: "ABC123",
        }
    ):
        response = test_client.get("/authenticate")

        assert response.json == {
            "authenticate": as_bool(authenticate_config),
            "providers": expected_providers,
        }


@pytest.fixture
def idinfo():
    return {
        "hd": "example.com",
        "given_name": "Ringo",
        "family_name": "Starr",
        "email": "ringo@example.com",
        "picture": "https://picture",
    }


def test_login_new_user(idinfo, test_client: flask.testing.FlaskClient):  # noqa: F811
    with mock_server_settings({ServerSettingsVar.GOOGLE_OAUTH_CLIENT_ID: "ABC123"}):
        with mock.patch(
            "google.oauth2.id_token.verify_oauth2_token", return_value=idinfo
        ):
            response = test_client.post("/login/google", json={"token": "abc"})

            returned_user = User.from_json_encodable(
                response.json["user"]  # type: ignore
            )

    saved_user = get_user("ringo@example.com")

    for user in (returned_user, saved_user):
        assert user.first_name == "Ringo"
        assert user.last_name == "Starr"
        assert user.email == "ringo@example.com"
        assert user.avatar_url == "https://picture"
        assert len(user.api_key) > 0


def test_login_existing_user(
    persisted_user: User, test_client: flask.testing.FlaskClient  # noqa: F811
):
    idinfo = {
        "hd": "example.com",
        "given_name": "George",
        "family_name": "Harrison",
        "email": "george@example.com",
        "picture": "https://new.avatar",
    }
    with mock_server_settings({ServerSettingsVar.GOOGLE_OAUTH_CLIENT_ID: "ABC123"}):
        with mock.patch(
            "google.oauth2.id_token.verify_oauth2_token", return_value=idinfo
        ):
            response = test_client.post("/login/google", json={"token": "abc"})

            returned_user = User.from_json_encodable(
                response.json["user"]  # type: ignore
            )

    updated_user = get_user("george@example.com")

    for user in (returned_user, updated_user):
        assert user.first_name == "George"
        assert user.last_name == "Harrison"
        assert user.email == "george@example.com"
        assert user.avatar_url == "https://new.avatar"
        assert user.api_key == persisted_user.api_key


def test_login_invalid_token(test_client: flask.testing.FlaskClient):  # noqa: F811
    def verify_oauth2_token(*args):
        raise GoogleAuthError()

    with mock_server_settings({ServerSettingsVar.GOOGLE_OAUTH_CLIENT_ID: "ABC123"}):
        with mock.patch(
            "google.oauth2.id_token.verify_oauth2_token",
            side_effect=verify_oauth2_token,
        ):
            response = test_client.post("/login/google", json={"token": "abc"})

            assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_login_invalid_domain(test_client: flask.testing.FlaskClient):  # noqa: F811
    with mock_server_settings(
        {
            ServerSettingsVar.GOOGLE_OAUTH_CLIENT_ID: "ABC123",
            ServerSettingsVar.SEMATIC_AUTHORIZED_EMAIL_DOMAIN: (
                "example1.com,example2.com"
            ),
        }
    ):
        with mock.patch(
            "google.oauth2.id_token.verify_oauth2_token",
            return_value={"hd": "wrong.domain"},
        ):
            response = test_client.post("/login/google", json={"token": "abc"})

            assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_login_valid_domain(
    idinfo, test_client: flask.testing.FlaskClient  # noqa: F811
):
    with mock_server_settings(
        {
            ServerSettingsVar.GOOGLE_OAUTH_CLIENT_ID: "ABC123",
            ServerSettingsVar.SEMATIC_AUTHORIZED_EMAIL_DOMAIN: (
                "example.com,example2.com"
            ),
        }
    ):
        with mock.patch(
            "google.oauth2.id_token.verify_oauth2_token",
            return_value=idinfo,
        ):
            response = test_client.post("/login/google", json={"token": "abc"})

            assert response.status_code == HTTPStatus.OK


@pytest.mark.skip(reason="Creating on-the-fly endpoints is fickle")
@pytest.mark.parametrize(
    "authenticate_config", ("True", "true", "1", "False", "false", "0")
)
def test_authenticate_decorator(
    authenticate_config: str,
    persisted_user: User,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    test_id = uuid.uuid4().hex

    with mock_server_settings(
        {ServerSettingsVar.SEMATIC_AUTHENTICATE: authenticate_config}
    ):

        def endpoint(user):
            if authenticate_config:
                assert user.email == persisted_user.email
            else:
                assert user is None

            return flask.Response()

        # Necessary to not confuse Flask
        endpoint.__name__ = "endpoint_{}".format(test_id)

        sematic_api.route("/test-{}".format(test_id))(authenticate(endpoint))

        headers = (
            {"X-API-KEY": persisted_user.api_key}
            if as_bool(authenticate_config)
            else {}
        )

        response = test_client.get(
            "/test-{}".format(test_id),
            headers=headers,
        )

        assert response.status_code == HTTPStatus.OK


@pytest.mark.skip(reason="Creating on-the-fly endpoints is fickle")
@pytest.mark.parametrize("headers", ({}, {"X-API-KEY": "abc"}))
def test_authenticate_decorator_fail(
    headers,
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    test_id = uuid.uuid4().hex

    with mock_server_settings({ServerSettingsVar.SEMATIC_AUTHENTICATE: "true"}):

        def endpoint(user):
            assert False

        # Necessary to not confuse Flask
        endpoint.__name__ = "endpoint_{}".format(test_id)

        sematic_api.route("/test-{}".format(test_id))(authenticate(endpoint))

        response = test_client.get("/test-{}".format(test_id), headers=headers)

        assert response.status_code == HTTPStatus.UNAUTHORIZED
