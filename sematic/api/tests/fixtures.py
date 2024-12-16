# Standard Library
import contextlib
import re
from copy import copy
from http import HTTPStatus
from typing import Dict, Type, cast
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
from sematic.abstract_plugin import (
    AbstractPlugin,
    AbstractPluginSettingsVar,
    PluginScope,
)

# Importing from server instead of app to make sure
# all endpoints are loaded
from sematic.api.server import sematic_api
from sematic.config.config import switch_env
from sematic.config.server_settings import ServerSettings, ServerSettingsVar
from sematic.config.settings import _DEFAULT_PROFILE, Settings, get_active_settings
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
        if (
            current_storage_scope is None
            and PluginScope.STORAGE in get_active_settings().scopes
        ):
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
                pattern=r"<\w+>",
                repl=r"\\w+",
                string=rule.rule,  # noqa: W605
            )
            url = re.compile(r"http:\/\/[\w\.]+:\d{1,5}" + path_to_match)
            for method in rule.methods:
                request_mock.add_callback(
                    callback=_request_callback, method=method, url=url
                )

        yield request_mock


@contextlib.contextmanager
def mock_plugin_settings(
    plugin: Type[AbstractPlugin], settings: Dict[AbstractPluginSettingsVar, str]
):
    # save copies of original global caches
    original_settings = settings_module._SETTINGS
    original_active_settings = settings_module._ACTIVE_SETTINGS

    # create new settings copy, which will be updated with the caller-specified settings
    new_settings = copy(original_settings) or Settings()

    # clear global caches
    # _ACTIVE_SETTINGS will be rehydrated on the first settings get call, so don't bother
    # to update its values
    settings_module._SETTINGS = new_settings
    settings_module._ACTIVE_SETTINGS = None

    # update the profile settings with the caller-specified settings
    new_profile_settings = new_settings.profiles[_DEFAULT_PROFILE].settings
    new_plugin_settings = new_profile_settings.get(plugin.get_path(), {})
    new_plugin_settings.update(settings)  # type: ignore
    new_profile_settings[plugin.get_path()] = new_plugin_settings

    try:
        yield settings
    finally:
        # reinstate original copies of global caches
        settings_module._SETTINGS = original_settings
        settings_module._ACTIVE_SETTINGS = original_active_settings


@contextlib.contextmanager
def mock_user_settings(settings: Dict[UserSettingsVar, str]):
    cast_settings = cast(Dict[AbstractPluginSettingsVar, str], settings)
    with mock_plugin_settings(UserSettings, cast_settings) as settings:
        yield settings


@contextlib.contextmanager
def mock_server_settings(settings: Dict[ServerSettingsVar, str]):
    cast_settings = cast(Dict[AbstractPluginSettingsVar, str], settings)
    with mock_plugin_settings(ServerSettings, cast_settings) as settings:
        yield settings


def make_auth_test(endpoint: str, method: str = "GET"):
    def test_auth(test_client: flask.testing.FlaskClient):
        with mock_server_settings({ServerSettingsVar.SEMATIC_AUTHENTICATE: "true"}):
            response = getattr(test_client, method.lower())(endpoint)
            assert response.status_code == HTTPStatus.UNAUTHORIZED

    return test_auth


@pytest.fixture
def mock_socketio():
    with (
        mock.patch("socketio.Client.connect"),
        mock.patch("sematic.api.endpoints.events._call_broadcast_endpoint"),
        mock.patch("sematic.api_client._notify_event"),
    ):
        yield


@pytest.fixture
def mock_auth():
    with mock_server_settings({ServerSettingsVar.SEMATIC_AUTHENTICATE: "false"}):
        yield


@pytest.fixture
def with_auth():
    with mock_server_settings({ServerSettingsVar.SEMATIC_AUTHENTICATE: "true"}):
        yield
