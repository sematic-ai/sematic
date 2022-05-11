# Third-party
import flask.testing

# Glow
from glow.api.tests.fixtures import test_client  # noqa: F401
from glow.db.tests.fixtures import test_db  # noqa: F401


def test_ping(test_client: flask.testing.FlaskClient):  # noqa: F811
    result = test_client.get("/api/v1/ping")
    assert result.json == {"status": "ok"}
