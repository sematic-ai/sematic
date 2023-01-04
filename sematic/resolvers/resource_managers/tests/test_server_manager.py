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

    resources = ServerResourceManager().resources_by_root_id(expected_root_id)
    resources = sorted(resources, key=lambda r: r.message)

    expected_resources = sorted(list(resources_by_id.values()), key=lambda r: r.message)
    assert expected_resources == resources
