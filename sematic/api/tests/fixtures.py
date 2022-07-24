# Standard library
import contextlib
import re
from urllib.parse import urljoin

# Third-party
import pytest
import werkzeug

# responses 0.21.0 has type stubs but they break mypy
# See https://github.com/getsentry/responses/issues/556
import responses  # type: ignore

# Sematic
from sematic.db.tests.fixtures import test_db, pg_mock  # noqa: F401
from sematic.config import get_config

# Importing from server instead of app to make sure
# all endpoints are loaded
from sematic.api.server import sematic_api


@pytest.fixture(scope="function")
def test_client(test_db):  # noqa: F811
    sematic_api.config["DATABASE"] = test_db
    sematic_api.config["TESTING"] = True

    with sematic_api.test_client() as client:
        yield client


# Credit to https://github.com/adamtheturtle/requests-mock-flask
@pytest.fixture  # noqa: F811
def mock_requests(test_client):
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

        yield


@contextlib.contextmanager
def do_authenticate(auth_config: bool):
    current_authenticate = get_config().authenticate
    try:
        get_config().authenticate = auth_config

        yield auth_config

    finally:
        get_config().authenticate = current_authenticate
