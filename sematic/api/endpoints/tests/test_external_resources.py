# Standard Library
import time
from collections import defaultdict
from dataclasses import dataclass, replace
from unittest.mock import patch

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


@dataclass(frozen=True)
class FailingTimedMessage(TimedMessage):
    def _do_update(self):
        if self.status.state == ResourceState.DEACTIVATING:
            raise ValueError("Intentional Fail")
        return super()._do_update()


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


def test_deactivate_orphaned(mock_auth, test_client):  # noqa: F811
    module = "sematic.api.endpoints.external_resources"

    message_kwargs = dict(
        allocation_seconds=0.0,
        deallocation_seconds=0.0,
        max_active_seconds=30.0,
    )
    with patch(f"{module}.get_orphaned_resource_records") as mock_get_orphans, patch(
        f"{module}.save_external_resource_record"
    ) as mock_save:
        resource1 = TimedMessage(**message_kwargs)
        record1 = ExternalResource.from_resource(resource1)

        resource2 = TimedMessage(**message_kwargs)
        resource2 = resource2.activate(is_local=False).update()
        record2 = ExternalResource.from_resource(resource2)

        resource3 = TimedMessage(**message_kwargs)
        resource3 = resource3.activate(is_local=False).update().deactivate().update()
        record3 = ExternalResource.from_resource(resource3)

        resource4 = FailingTimedMessage(**message_kwargs)
        resource4 = resource4.activate(is_local=False).update().deactivate()
        record4 = ExternalResource.from_resource(resource4)

        mock_get_orphans.return_value = [
            record1,
            record2,
            record3,
            record4,
        ]
        result = test_client.post("/api/v1/external_resources/all/clean_orphaned")
        saves_by_resource_id = defaultdict(list)
        for call in mock_save.call_args_list:
            saves_by_resource_id[call[0][0].id].append(call[0][0])

        assert saves_by_resource_id[record1.id][-1].resource_state.is_terminal()
        assert saves_by_resource_id[record2.id][-1].resource_state.is_terminal()
        assert len(saves_by_resource_id[record3.id]) == 0
        assert len(saves_by_resource_id[record4.id]) == 0

        assert result.json == {
            "state_changes": {
                "deactivated": [resource1.id, resource2.id],
                "forced_terminal": [],
                "unmodified": [resource3.id],
                "update_error": [resource4.id],
            }
        }

        mock_save.reset_mock()
        result = test_client.post(
            "/api/v1/external_resources/all/clean_orphaned?force=true"
        )
        assert result.json["state_changes"]["forced_terminal"] == [resource4.id]
        saves_by_resource_id = defaultdict(list)
        for call in mock_save.call_args_list:
            saves_by_resource_id[call[0][0].id].append(call[0][0])
        assert saves_by_resource_id[record4.id][-1].resource_state.is_terminal()
