# Third-party
import flask.testing

# Sematic
from sematic.api.tests.fixtures import test_client  # noqa: F401
from sematic.db.tests.fixtures import test_db, pg_mock  # noqa: F401


def test_ping(test_client: flask.testing.FlaskClient):  # noqa: F811
    result = test_client.get("/api/v1/ping")
    assert result.json == {"status": "ok"}
