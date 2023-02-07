# Standard Library
from typing import Any, Dict

# Third-party
import flask.testing

# Sematic
from sematic.api.tests.fixtures import mock_auth, test_client  # noqa: F401
from sematic.db.models.artifact import Artifact
from sematic.db.tests.fixtures import persisted_artifact, test_db  # noqa: F401
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
