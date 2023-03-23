# Standard Library
from urllib.parse import urlparse

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
    parsed_url = urlparse(destination.uri)

    assert parsed_url.scheme == "sematic"

    response = test_client.put(parsed_url.path, data=value)

    assert response.status_code == 200

    destination = memory_storage.get_read_destination("artifacts", "123", None)
    parsed_url = urlparse(destination.uri)

    assert parsed_url.scheme == "sematic"

    response = test_client.get(parsed_url.path)

    assert response.data == value
