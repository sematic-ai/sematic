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

    destination = memory_storage.get_write_destination("artifacts", "123", None)

    response = test_client.put(destination.url, data=value)

    assert response.status_code == 200

    destination = memory_storage.get_read_destination("artifacts", "123", None)

    response = test_client.get(destination.url)

    assert response.data == value
