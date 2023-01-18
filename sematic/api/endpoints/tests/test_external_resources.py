# Standard Library
import time
from dataclasses import replace

# Third-party
import flask.testing

# Sematic
from sematic.api.tests.fixtures import (  # noqa: F401
    make_auth_test,
    mock_auth,
    test_client,
)
from sematic.db.models.external_resource import ExternalResource
from sematic.db.tests.fixtures import (  # noqa: F401
    persisted_external_resource,
    persisted_run,
    persisted_user,
    run,
    test_db,
)
from sematic.plugins.abstract_external_resource import (
    AbstractExternalResource,
    ManagedBy,
    ResourceState,
    ResourceStatus,
)
from sematic.plugins.external_resource.timed_message import TimedMessage

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
    my_resource = AbstractExternalResource(
        status=ResourceStatus(state=ResourceState.CREATED, message="hi!")
    )
    record = ExternalResource.from_resource(my_resource)
    payload = {"external_resource": record.to_json_encodable()}
    response = test_client.post("/api/v1/external_resources", json=payload)
    assert response.status_code == 200

    response = test_client.get(f"/api/v1/external_resources/{record.id}")
    assert response.status_code == 200
    from_api_record = ExternalResource.from_json_encodable(
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
    record = ExternalResource.from_resource(my_resource_activating)
    payload = {"external_resource": record.to_json_encodable()}
    response = test_client.post("/api/v1/external_resources", json=payload)
    assert response.status_code == 200
    from_api_record = ExternalResource.from_json_encodable(
        response.json["external_resource"]  # type: ignore
    )
    assert from_api_record.history == (my_resource_activating, my_resource)


def test_activate_deactivate(
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    my_resource = TimedMessage(
        allocation_seconds=0.0,
        deallocation_seconds=0.0,
        max_active_seconds=30.0,
    )
    record = ExternalResource.from_resource(my_resource)
    payload = {"external_resource": record.to_json_encodable()}
    response = test_client.post("/api/v1/external_resources", json=payload)
    assert response.status_code == 200

    activating_response = test_client.post(
        f"/api/v1/external_resources/{my_resource.id}/activate"
    )
    assert activating_response.status_code == 200
    activating = ExternalResource.from_json_encodable(
        activating_response.json["external_resource"]  # type: ignore
    )
    assert activating.resource_state == ResourceState.ACTIVATING

    is_active = False
    time_started = time.time()

    while not is_active:
        time_passed = time.time() - time_started
        assert time_passed < 5
        response = test_client.get(
            f"/api/v1/external_resources/{record.id}?refresh_remote=true"
        )
        assert response.status_code == 200
        from_api_record = ExternalResource.from_json_encodable(
            response.json["external_resource"]  # type: ignore
        )
        is_active = from_api_record.resource_state == ResourceState.ACTIVE

    deactivating_response = test_client.post(
        f"/api/v1/external_resources/{my_resource.id}/deactivate"
    )
    assert deactivating_response.status_code == 200
    deactivating = ExternalResource.from_json_encodable(
        deactivating_response.json["external_resource"]  # type: ignore
    )
    assert deactivating.resource_state == ResourceState.DEACTIVATING

    is_deactivated = False
    time_started = time.time()

    while not is_deactivated:
        time_passed = time.time() - time_started
        assert time_passed < 5
        response = test_client.get(
            f"/api/v1/external_resources/{record.id}?refresh_remote=true"
        )
        assert response.status_code == 200
        from_api_record = ExternalResource.from_json_encodable(
            response.json["external_resource"]  # type: ignore
        )
        is_deactivated = from_api_record.resource_state == ResourceState.DEACTIVATED

    # trying to deactivate again should leave it unmodified
    deactivated_response = test_client.post(
        f"/api/v1/external_resources/{my_resource.id}/deactivate"
    )
    assert deactivated_response.status_code == 200
    deactivated = ExternalResource.from_json_encodable(
        deactivated_response.json["external_resource"]  # type: ignore
    )
    assert deactivated.resource_state == ResourceState.DEACTIVATED
