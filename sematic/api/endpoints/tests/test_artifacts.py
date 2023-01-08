# Standard Library
from typing import Any, Dict
from unittest import mock

# Third-party
import flask.testing

# Sematic
from sematic.api.tests.fixtures import mock_auth, test_client  # noqa: F401
from sematic.db.models.artifact import Artifact
from sematic.db.tests.fixtures import persisted_artifact, test_db  # noqa: F401
from sematic.plugins.storage.memory_storage import MemoryStorage
from sematic.plugins.storage.s3_storage import S3Storage
from sematic.tests.fixtures import test_storage  # noqa: F401


def test_get_artifact_endpoint(
    mock_auth,  # noqa: F811
    persisted_artifact: Artifact,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    response = test_client.get(f"/api/v1/artifacts/{persisted_artifact.id}")

    payload: Dict[str, Any] = response.json  # type: ignore

    artifact = Artifact.from_json_encodable(payload["content"])

    assert artifact.id == persisted_artifact.id


@mock.patch(
    "sematic.api.endpoints.artifacts.get_active_plugins", return_value=[MemoryStorage]
)
def test_upload_download(
    mock_plugin,
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    value = b"foo"

    response = test_client.get("/api/v1/artifacts/123/location")
    assert response.status_code == 200

    location = response.json["location"]  # type: ignore

    response = test_client.put(f"/api/v1{location}", data=value)
    assert response.status_code == 200

    response = test_client.get("/api/v1/artifacts/123/data")
    assert response.status_code == 200

    assert response.data == value


@mock.patch(
    "sematic.api.endpoints.artifacts.get_active_plugins", return_value=[S3Storage]
)
def test_redirect_download(
    mock_plugin,
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    with mock.patch(
        "sematic.plugins.storage.s3_storage.S3Storage._make_presigned_url",
        return_value="https://presigned-url",
    ):
        response = test_client.get("/api/v1/artifacts/123/data")

        assert response.status_code == 302
