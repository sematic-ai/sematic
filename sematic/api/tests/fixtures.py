# Standard Library
import contextlib
import re
import tempfile
from http import HTTPStatus
from typing import Any, Generator, Optional
from unittest import mock
from urllib.parse import urljoin

# Third-party
import flask.testing
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
def _mock_settings_file(file_path: Optional[str]) -> Generator[Any, Any, None]:

    with tempfile.NamedTemporaryFile("w") as tf:

        if file_path is not None:
            with open(file_path, "r") as f:
                tf.write(f.read())
                tf.flush()

        with mock.patch(
            "sematic.user_settings._get_settings_file",
            return_value=tf.name,
            new_callable=mock.PropertyMock,
        ):
            # set up: invalidate the existing settings cache, if any
            user_settings._settings = None

            yield tf

            # tear down: invalidate the mock settings cache
            # it will be populated from the settings file on the next invocation
            user_settings._settings = None


@pytest.fixture(scope="function")
def mock_settings_file(request: Any) -> Generator[Any, Any, None]:
    """
    An indirect fixture used to create a temporary file copy of a user settings file which
    will supplant the actual settings file, and which can be safely altered when invoking
    user settings operations.

    Example
    -------
    @pytest.mark.parametrize("mock_settings_file", ["/my/settings.yaml"], indirect=True)
    def my_test(mock_settings_file):

        # theoretical usage:
        with open("~/.sematic/settings.yaml", "r") as f:
            # this will find the contents of "/my/settings.yaml"
            # in "~/.sematic/settings.yaml"
            f.read()

        # more realistic usage:
        user_settings._load_settings()

        # theoretical usage:
        with open("~/.sematic/settings.yaml", "w") as f:
            # this will write to the mock file copy
            # after my_test finishes execution, the original "~/.sematic/settings.yaml"
            # file will be untouched
            f.write("ruin the mock file copy")

        # more realistic usage:
        user_settings._save_settings(UserSettings([...]))
    """
    file_path = None
    # request.param will hold the name of the data file to use
    # to populate the contents of the temp file
    if request is not None and request.param is not None:
        file_path = request.param

    with _mock_settings_file(file_path):
        yield


@contextlib.contextmanager
def mock_user_settings(settings: user_settings.ProfileSettingsType):
    with _mock_settings_file(None):
        # set up: invalidate the existing settings cache, if any,
        # and build the mock settings
        for var, value in settings.items():
            user_settings.set_user_settings(var, value)

        yield


def make_auth_test(endpoint: str, method: str = "GET"):
    def test_auth(test_client: flask.testing.FlaskClient):
        with mock_user_settings(
            {user_settings.SettingsVar.SEMATIC_AUTHENTICATE: "true"}
        ):
            response = getattr(test_client, method.lower())(endpoint)
            assert response.status_code == HTTPStatus.UNAUTHORIZED

    return test_auth


@pytest.fixture
def mock_socketio():
    with mock.patch("socketio.Client.connect"):
        yield


@pytest.fixture
def mock_auth():
    with mock_user_settings({user_settings.SettingsVar.SEMATIC_AUTHENTICATE: "false"}):
        yield
