# Standard Library
import tempfile
from unittest import mock
from urllib.parse import urlparse

# Third-party
import flask.testing

# Sematic
from sematic.api.tests.fixtures import (
    mock_auth,  # noqa: F401
    mock_plugin_settings,  # noqa: F401
    test_client,  # noqa: F401; noqa: F401
)
from sematic.config.config import get_config
from sematic.config.tests.fixtures import empty_settings_file  # noqa: F401
from sematic.db.tests.fixtures import test_db  # noqa: F401
from sematic.plugins.storage.local_storage import (
    LocalStorage,
    LocalStorageSettingsVar,
    _get_data_dir,
)


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
            destination = local_storage.get_write_destination("artifacts", "123", None)
            parsed_url = urlparse(destination.uri)

            assert parsed_url.scheme == "sematic"

            response = test_client.put(parsed_url.path, data=value)

            assert response.status_code == 200

            destination = local_storage.get_read_destination("artifacts", "123", None)
            parsed_url = urlparse(destination.uri)

            assert parsed_url.scheme == "sematic"

            response = test_client.get(parsed_url.path)

            assert response.data == value


def test_settings():
    with mock_plugin_settings(
        LocalStorage, {LocalStorageSettingsVar.LOCAL_STORAGE_PATH: "/foo/bar"}
    ):
        assert _get_data_dir() == "/foo/bar"


def test_default_settings(empty_settings_file):  # noqa: F811
    assert _get_data_dir() == get_config().data_dir
