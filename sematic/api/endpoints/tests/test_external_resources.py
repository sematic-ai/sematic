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
from sematic.db.models.user import User  # noqa: F401
from sematic.db.queries import (  # noqa: F401
    save_external_resource_record,
    save_run_external_resource_link,
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

test_list_external_resource_auth = make_auth_test(
    "/api/v1/external_resources/ids", method="GET"
)
test_get_external_resource_auth = make_auth_test(
    "/api/v1/external_resources/abc123", method="GET"
)
test_set_external_resource_auth = make_auth_test(
    "/api/v1/external_resources/abc123", method="POST"
)


def test_list_external_resources_empty(
    mock_auth, test_client: flask.testing.FlaskClient  # noqa: F811
):
    response = test_client.get("/api/v1/external_resources/ids?root_id=abc123")
    assert response.status_code == 200

    assert response.json == dict(resource_ids=[])


def test_list_external_resource_ids(
    mock_auth,  # noqa: F811
    persisted_run,  # noqa: F811
    persisted_external_resource,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    save_run_external_resource_link(persisted_external_resource.id, persisted_run.id)
    response = test_client.get(
        f"/api/v1/external_resources/ids?root_id={persisted_run.id}"
    )
    assert response.status_code == 200

    assert response.json == dict(resource_ids=[persisted_external_resource.id])


def test_save_read(
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    my_resource = ExternalResource(
        status=ResourceStatus(state=ResourceState.CREATED, message="hi!")
    )
    record = ExternalResourceRecord.from_resource(my_resource)
    payload = {"record": record.to_json_encodable()}
    response = test_client.post(f"/api/v1/external_resources/{record.id}", json=payload)
    assert response.status_code == 200

    response = test_client.get(f"/api/v1/external_resources/{record.id}")
    assert response.status_code == 200
    from_api_record = ExternalResourceRecord.from_json_encodable(
        response.json["record"]  # type: ignore
    )
    assert from_api_record.resource == my_resource

    my_resource_activating = replace(
        my_resource,
        status=ResourceStatus(
            state=ResourceState.ACTIVATING,
            message="firing up my lasers",
            managed_by=ManagedBy.REMOTE,
        ),
    )
    assert my_resource_activating != my_resource
    record = ExternalResourceRecord.from_resource(my_resource_activating)
    payload = {"record": record.to_json_encodable()}
    response = test_client.post(f"/api/v1/external_resources/{record.id}", json=payload)
    assert response.status_code == 200
    from_api_record = ExternalResourceRecord.from_json_encodable(
        response.json["record"]  # type: ignore
    )
    assert from_api_record.history == (my_resource_activating, my_resource)
