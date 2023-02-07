# Third-party
import flask
import flask.testing

# Sematic
from sematic.api.tests.fixtures import mock_auth, test_client  # noqa: F401
from sematic.db.tests.fixtures import test_db  # noqa: F401


def test_upload_download(
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    value = b"foo"

    response = test_client.get("/api/v1/storage/artifacts/123/location")
    assert response.status_code == 200

    url = response.json["url"]  # type: ignore

    response = test_client.put(url, data=value)
    assert response.status_code == 200

    response = test_client.get("/api/v1/storage/artifacts/123/data")
    assert response.status_code == 302

    response = test_client.get("/api/v1/storage/artifacts/123/memory")

    assert response.data == value
