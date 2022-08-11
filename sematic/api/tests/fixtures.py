# Standard Library
import contextlib
import functools
import re
from http import HTTPStatus
from typing import Any, Callable, Dict
from urllib.parse import urljoin

import flask.testing

# Third-party
import pytest

# responses 0.21.0 has type stubs but they break mypy
# See https://github.com/getsentry/responses/issues/556
import responses  # type: ignore
import werkzeug

# Sematic
import sematic.user_settings as user_settings

# Importing from server instead of app to make sure
# all endpoints are loaded
from sematic.api.server import sematic_api
from sematic.config import get_config, switch_env
from sematic.db.tests.fixtures import pg_mock, test_db  # noqa: F401


@pytest.fixture(scope="function")
def test_client(test_db):  # noqa: F811
    sematic_api.config["DATABASE"] = test_db
    sematic_api.config["TESTING"] = True

    with sematic_api.test_client() as client:
        yield client


# Credit to https://github.com/adamtheturtle/requests-mock-flask
@pytest.fixture  # noqa: F811
def mock_requests(test_client):
    # This mock will place calls to an in-memory server, local configurations
    # are the appropriate match.
    switch_env("local")

    def _request_callback(request):
        environ_builder = werkzeug.test.EnvironBuilder(
            path=request.path_url,
            method=str(request.method),
            headers=dict(request.headers),
            data=request.body,
        )
        environ = environ_builder.get_environ()

        if "Content-Length" in request.headers:
            environ["CONTENT_LENGTH"] = request.headers["Content-Length"]

        response = test_client.open(environ)

        return response.status_code, dict(response.headers), response.data

    api_url = get_config().api_url
    with responses.RequestsMock(assert_all_requests_are_fired=False) as request_mock:
        for rule in sematic_api.url_map.iter_rules():
            path_to_match = re.sub(
                pattern=r"<\w+>", repl="\\\w+", string=rule.rule  # noqa: W605
            )
            pattern = urljoin(api_url, path_to_match)
            url = re.compile(pattern)
            for method in rule.methods:
                request_mock.add_callback(
                    callback=_request_callback, method=method, url=url
                )

        yield request_mock


@contextlib.contextmanager
def mock_user_settings(settings: Dict[user_settings.SettingsVar, Any]):
    # Force load everything first
    user_settings.get_all_user_settings()

    original_settings = user_settings._settings

    user_settings._settings = {
        "default": {key.value: value for key, value in settings.items()}
    }

    try:
        yield settings
    finally:
        user_settings._settings = original_settings


def mock_no_auth(fn: Callable) -> Callable:
    @functools.wraps(fn)
    def no_auth_fn(*args, **kwargs):
        with mock_user_settings(
            {user_settings.SettingsVar.SEMATIC_AUTHENTICATE: False}
        ):
            fn(*args, **kwargs)

    return no_auth_fn


def make_auth_test(endpoint: str, method: str = "GET"):
    def test_auth(test_client: flask.testing.FlaskClient):
        with mock_user_settings({user_settings.SettingsVar.SEMATIC_AUTHENTICATE: True}):
            response = getattr(test_client, method.lower())(endpoint)
            assert response.status_code == HTTPStatus.UNAUTHORIZED

    return test_auth
