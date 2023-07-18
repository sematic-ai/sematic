# Standard Library
from dataclasses import dataclass, field
from datetime import timedelta
from typing import List, Tuple
from unittest import mock

# Third-party
import flask.testing

# Sematic
from sematic.api.tests.fixtures import mock_auth, test_client  # noqa: F401
from sematic.db.tests.fixtures import test_db  # noqa: F401
from sematic.plugins.storage.gcs_storage import GcsClientMethod, GcsStorage


@dataclass
class Blob:
    name: str
    contents: bytes
    generation_requests: List[Tuple[timedelta, str, str]] = field(default_factory=list)

    def generate_signed_url(
        self,
        expiration,
        method,
        version,
    ):
        self.generation_requests.append((expiration, method, version))
        return f"http://storage.com/{self.name}?signature=abc123"


@dataclass
class FakeBucket:
    name: str
    blobs: List[Blob]

    def blob(self, key) -> Blob:
        return next(blob for blob in self.blobs if blob.name == key)


class FakeBucketStorage(GcsStorage):
    def __init__(self, bucket):
        self.bucket = bucket

    @property
    def _bucket(self):
        return self.bucket


def test_upload_download(
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    gcs_storage = GcsStorage()

    with mock.patch(
        "sematic.plugins.storage.gcs_storage.GcsStorage._make_presigned_url",
        return_value="https://presigned-url",
    ):
        destination = gcs_storage.get_write_destination("artifacts", "123", None)

        assert destination.uri == "https://presigned-url"

        destination = gcs_storage.get_read_destination("artifacts", "123", None)

        assert destination.uri == "https://presigned-url"


def test_make_presigned_url(
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    key = "my-key"
    bucket_name = "my-bucket"
    contents = b"hello\nto\n\the\nwhole\nworld"
    generation_requests: List[Tuple[timedelta, str, str]] = []
    blob = Blob(name=key, contents=contents, generation_requests=generation_requests)
    gcs_storage = FakeBucketStorage(FakeBucket(name=bucket_name, blobs=[blob]))

    url = gcs_storage._make_presigned_url(GcsClientMethod.GET, key=key)
    assert key in url
    assert len(generation_requests) == 1
    time, method, _ = generation_requests[0]
    assert time == timedelta(minutes=5)
    assert method == "GET"
