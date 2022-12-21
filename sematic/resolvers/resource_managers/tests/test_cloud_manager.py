# Standard Library
from unittest.mock import patch

# Third-party
import pytest

# Sematic
from sematic.external_resource_plugins.timed_message import TimedMessage
from sematic.resolvers.resource_managers.cloud_manager import CloudResourceManager


@pytest.fixture
def mock_api_client():
    with patch("sematic.resolvers.resource_managers.cloud_manager.api_client") as api:
        yield api


def test_resources_by_root_id(mock_api_client):
    expected_root_id = "abc123"
    resources_by_id = {
        "a": TimedMessage(message="a"),
        "b": TimedMessage(message="b"),
        "c": TimedMessage(message="c"),
    }

    def mock_get_ids(run_id):
        assert run_id == expected_root_id
        return resources_by_id.keys()

    def mock_get_external_resource(resource_id):
        return resources_by_id[resource_id]

    mock_api_client.get_resource_ids_by_root_run_id = mock_get_ids
    mock_api_client.get_external_resource = mock_get_external_resource

    resources = CloudResourceManager().resources_by_root_id(expected_root_id)
    resources = sorted(resources, key=lambda r: r.message)

    expected_resources = sorted(list(resources_by_id.values()), key=lambda r: r.message)
    assert expected_resources == resources
