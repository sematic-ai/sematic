# Standard Library
import contextlib
import re
from copy import copy
from http import HTTPStatus
from typing import Dict, cast
from unittest import mock

# Third-party
import flask.testing
import pytest

# responses 0.21.0 has type stubs, but they break mypy
# See https://github.com/getsentry/responses/issues/556
import responses  # type: ignore
import werkzeug

# Sematic
import sematic.config.settings as settings_module
from sematic.abstract_plugin import PluginScope

# Importing from server instead of app to make sure
# all endpoints are loaded
from sematic.api.server import sematic_api
from sematic.config.config import switch_env
from sematic.config.server_settings import ServerSettings, ServerSettingsVar
from sematic.config.settings import (
    _DEFAULT_PROFILE,
    PluginSettings,
    Settings,
    get_active_settings,
)
from sematic.config.user_settings import UserSettings, UserSettingsVar
from sematic.db.tests.fixtures import pg_mock, test_db  # noqa: F401
from sematic.plugins.storage.memory_storage import MemoryStorage


@pytest.fixture
def mock_storage():
    with _mock_storage() as storage:
        yield storage


@contextlib.contextmanager
def _mock_storage():
    current_storage_scope = get_active_settings().scopes.get(PluginScope.STORAGE)
    get_active_settings().scopes[PluginScope.STORAGE] = [f"{MemoryStorage.get_path()}"]

    try:
        yield MemoryStorage
    finally:
        if current_storage_scope is None:
            del get_active_settings().scopes[PluginScope.STORAGE]
        else:
            get_active_settings().scopes[PluginScope.STORAGE] = current_storage_scope


@pytest.fixture(scope="function")
def test_client(test_db):  # noqa: F811
    sematic_api.config["DATABASE"] = test_db
    sematic_api.config["TESTING"] = True

    with _mock_storage():
        with sematic_api.test_client() as client:
            yield client


# Credit to https://github.com/adamtheturtle/requests-mock-flask
@pytest.fixture  # noqa: F811
def mock_requests(test_client):
    # This mock will place calls to an in-memory server, local configurations
    # are the appropriate match.
    switch_env("test")

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

        response = test_client.open(environ, follow_redirects=True)

        return response.status_code, dict(response.headers), response.data

    with responses.RequestsMock(assert_all_requests_are_fired=False) as request_mock:
        for rule in sematic_api.url_map.iter_rules():
            path_to_match = re.sub(
                pattern=r"<\w+>", repl="\\\w+", string=rule.rule  # noqa: W605
            )
            url = re.compile(r"http:\/\/[\w\.]+:\d{1,5}" + path_to_match)
            for method in rule.methods:
                request_mock.add_callback(
                    callback=_request_callback, method=method, url=url
                )

        yield request_mock


@contextlib.contextmanager
def mock_user_settings(settings: Dict[UserSettingsVar, str]):
    original_settings = settings_module._SETTINGS

    original_settings_copy = copy(original_settings)
    if original_settings_copy is None:
        original_settings_copy = Settings()

    plugin_settings = cast(PluginSettings, settings)
    user_settings = original_settings_copy.profiles[_DEFAULT_PROFILE].settings.get(
        UserSettings.get_path(), {}
    )

    for key, value in plugin_settings.items():
        user_settings[key] = value

    original_settings_copy.profiles[_DEFAULT_PROFILE].settings[
        UserSettings.get_path()
    ] = plugin_settings

    settings_module._SETTINGS = original_settings_copy

    try:
        yield settings
    finally:
        settings_module._SETTINGS = original_settings


@contextlib.contextmanager
def mock_server_settings(settings: Dict[ServerSettingsVar, str]):
    original_settings = settings_module._SETTINGS

    original_settings_copy = copy(original_settings)
    if original_settings_copy is None:
        original_settings_copy = Settings()

    plugin_settings = cast(PluginSettings, settings)
    user_settings = original_settings_copy.profiles[_DEFAULT_PROFILE].settings.get(
        ServerSettings.get_path(), {}
    )

    for key, value in plugin_settings.items():
        user_settings[key] = value

    original_settings_copy.profiles[_DEFAULT_PROFILE].settings[
        ServerSettings.get_path()
    ] = plugin_settings

    settings_module._SETTINGS = original_settings_copy

    try:
        yield settings
    finally:
        settings_module._SETTINGS = original_settings


def make_auth_test(endpoint: str, method: str = "GET"):
    def test_auth(test_client: flask.testing.FlaskClient):
        with mock_server_settings({ServerSettingsVar.SEMATIC_AUTHENTICATE: "true"}):
            response = getattr(test_client, method.lower())(endpoint)
            assert response.status_code == HTTPStatus.UNAUTHORIZED

    return test_auth


@pytest.fixture
def mock_socketio():
    with mock.patch("socketio.Client.connect"):
        yield


@pytest.fixture
def mock_auth():
    with mock_server_settings({ServerSettingsVar.SEMATIC_AUTHENTICATE: "false"}):
        yield
