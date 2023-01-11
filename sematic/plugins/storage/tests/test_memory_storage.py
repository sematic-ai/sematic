# Third-party
import flask.testing

# Sematic
from sematic.api.tests.fixtures import mock_auth, test_client  # noqa: F401
from sematic.db.tests.fixtures import test_db  # noqa: F401
from sematic.plugins.storage.memory_storage import MemoryStorage


def test_upload(
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    value = b"foo"

    memory_storage = MemoryStorage()

    location = memory_storage.get_write_location("artifacts", "123")

    response = test_client.put(f"/api/v1{location}", data=value)

    assert response.status_code == 200

    read_payload = memory_storage.get_read_payload("artifacts", "123")

    assert read_payload.content == value
