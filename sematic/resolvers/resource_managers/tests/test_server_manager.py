# Standard Library
from unittest.mock import patch

# Third-party
import pytest

# Sematic
from sematic.plugins.external_resource.timed_message import TimedMessage
from sematic.resolvers.resource_managers.server_manager import ServerResourceManager


@pytest.fixture
def mock_api_client():
    with patch("sematic.resolvers.resource_managers.server_manager.api_client") as api:
        yield api


def test_resources_by_root_id(mock_api_client):
    expected_root_id = "abc123"
    resources_by_id = {
        "a": TimedMessage(message="a"),
        "b": TimedMessage(message="b"),
        "c": TimedMessage(message="c"),
    }

    def mock_get_resources_by_root(run_id):
        assert run_id == expected_root_id
        return resources_by_id.values()

    def mock_get_external_resource(resource_id, refresh_remote):
        return resources_by_id[resource_id]

    mock_api_client.get_resources_by_root_run_id = mock_get_resources_by_root
    mock_api_client.get_external_resource = mock_get_external_resource

    resources = ServerResourceManager(10).resources_by_root_id(expected_root_id)
    resources = sorted(resources, key=lambda r: r.message)

    expected_resources = sorted(list(resources_by_id.values()), key=lambda r: r.message)
    assert expected_resources == resources


def test_poll_for_updates_by_resource_id():
    resource_manager = ServerResourceManager(0.5)

    original1 = TimedMessage(
        allocation_seconds=0.0,
        deallocation_seconds=0.0,
        max_active_seconds=10.0,
    )
    activating1 = original1.activate(is_local=False)
    activated1 = activating1.update()
    deactivating1 = activated1.deactivate()
    deactivated1 = deactivating1.update()

    original2 = TimedMessage(
        allocation_seconds=0.0,
        deallocation_seconds=0.0,
        max_active_seconds=10.0,
    )
    activating2 = original2.activate(is_local=False)
    activated2 = activating2.update()
    deactivating2 = activated2.deactivate()
    deactivated2 = deactivating2.update()

    get_resource_results = {
        original1.id: [
            original1,
            activating1,
            activated1,
            deactivating1,
            deactivated1,
        ],
        original2.id: [
            original2,
            activating2,
            activated2,
            deactivating2,
            deactivated2,
        ],
    }

    def fake_get_resource(resource_id):
        to_return = get_resource_results[resource_id][0]
        if len(get_resource_results[resource_id]) > 1:
            get_resource_results[resource_id].remove(to_return)
        return to_return

    resource_manager.get_resource_for_id = fake_get_resource

    thread1 = resource_manager.poll_for_updates_by_resource_id(original1.id)
    thread2 = resource_manager.poll_for_updates_by_resource_id(original2.id)

    assert thread1 is not None
    assert thread2 is None
    thread1.join(5)  # thread should terminate once it detects resources are terminal

    # it should have kept calling for updates until it got to the results with the
    # terminal states
    assert len(get_resource_results[original1.id]) == 1
    assert len(get_resource_results[original2.id]) == 1
