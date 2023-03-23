# Standard Library
from unittest import mock

# Third-party
import flask.testing

# Sematic
from sematic.api.tests.fixtures import mock_auth, test_client  # noqa: F401
from sematic.db.tests.fixtures import test_db  # noqa: F401
from sematic.plugins.storage.s3_storage import S3Storage


def test_upload_download(
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    s3_storage = S3Storage()

    with mock.patch(
        "sematic.plugins.storage.s3_storage.S3Storage._make_presigned_url",
        return_value="https://presigned-url",
    ):
        destination = s3_storage.get_write_destination("artifacts", "123", None)

        assert destination.uri == "https://presigned-url"

        destination = s3_storage.get_read_destination("artifacts", "123", None)

        assert destination.uri == "https://presigned-url"
