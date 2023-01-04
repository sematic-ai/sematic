# Standard Library
from dataclasses import replace

# Third-party
import flask.testing

# Sematic
from sematic.api.tests.fixtures import (  # noqa: F401
    make_auth_test,
    mock_auth,
    test_client,
)
from sematic.db.models.external_resource import (
    ExternalResource as ExternalResourceRecord,
)
from sematic.db.tests.fixtures import (  # noqa: F401
    persisted_external_resource,
    persisted_run,
    persisted_user,
    run,
    test_db,
)
from sematic.external_resource import (
    ExternalResource,
    ManagedBy,
    ResourceState,
    ResourceStatus,
)

test_get_external_resource_auth = make_auth_test(
    "/api/v1/external_resources/abc123", method="GET"
)
test_set_external_resource_auth = make_auth_test(
    "/api/v1/external_resources", method="POST"
)


def test_save_read(
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    my_resource = ExternalResource(
        status=ResourceStatus(state=ResourceState.CREATED, message="hi!")
    )
    record = ExternalResourceRecord.from_resource(my_resource)
    payload = {"external_resource": record.to_json_encodable()}
    response = test_client.post("/api/v1/external_resources", json=payload)
    assert response.status_code == 200

    response = test_client.get(f"/api/v1/external_resources/{record.id}")
    assert response.status_code == 200
    from_api_record = ExternalResourceRecord.from_json_encodable(
        response.json["external_resource"]  # type: ignore
    )
    assert from_api_record.resource == my_resource

    my_resource_activating = replace(
        my_resource,
        status=ResourceStatus(
            state=ResourceState.ACTIVATING,
            message="firing up my lasers",
            managed_by=ManagedBy.SERVER,
        ),
    )
    assert my_resource_activating != my_resource
    record = ExternalResourceRecord.from_resource(my_resource_activating)
    payload = {"external_resource": record.to_json_encodable()}
    response = test_client.post("/api/v1/external_resources", json=payload)
    assert response.status_code == 200
    from_api_record = ExternalResourceRecord.from_json_encodable(
        response.json["external_resource"]  # type: ignore
    )
    assert from_api_record.history == (my_resource_activating, my_resource)
