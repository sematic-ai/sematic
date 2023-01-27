# Standard Library
import tempfile
from unittest import mock

# Third-party
import flask.testing

# Sematic
from sematic.api.tests.fixtures import mock_auth, test_client  # noqa: F401
from sematic.db.tests.fixtures import test_db  # noqa: F401
from sematic.plugins.storage.local_storage import LocalStorage


def test_upload_download(
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    value = b"foo"

    local_storage = LocalStorage()

    with tempfile.TemporaryDirectory() as tempdir:
        with mock.patch(
            "sematic.plugins.storage.local_storage._get_data_dir", return_value=tempdir
        ):
            location = local_storage.get_write_location("artifacts", "123", None)
            response = test_client.put(location.location, data=value)

            assert response.status_code == 200

            read_location = local_storage.get_read_location("artifacts", "123", None)

            response = test_client.get(read_location.location)

            assert response.data == value
