# Standard Library
from unittest import mock

# Third-party
import flask
import flask.testing

# Sematic
from sematic.api.tests.fixtures import mock_auth, test_client  # noqa: F401
from sematic.db.tests.fixtures import test_db  # noqa: F401
from sematic.plugins.storage.memory_storage import MemoryStorage


@mock.patch(
    "sematic.api.endpoints.uploads._get_storage_plugin", return_value=MemoryStorage
)
def test_upload_download(
    mock_plugin,
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    value = b"foo"

    response = test_client.get("/api/v1/uploads/artifacts/123/location")
    assert response.status_code == 200

    location = response.json["location"]  # type: ignore

    response = test_client.put(location, data=value)
    assert response.status_code == 200

    response = test_client.get("/api/v1/uploads/artifacts/123/data")
    assert response.status_code == 302

    response = test_client.get("/api/v1/uploads/artifacts/123/memory")

    assert response.data == value
