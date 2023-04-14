# Standard Library
from unittest.mock import patch

# Sematic
from sematic.db.models.external_resource import ExternalResource
from sematic.plugins.external_resource.timed_message import TimedMessage


@patch("sematic.types.types.dataclass.type_from_json_encodable")
def test_force_to_terminal_state(mock_type_from_encodable):
    resource = ExternalResource.from_resource(TimedMessage(message="doesn't matter"))
    mock_type_from_encodable.side_effect = ValueError(
        "Emulating error deserializing moved type"
    )

    message = "testing force to terminal"
    resource.force_to_terminal_state(message)

    assert resource.resource_state.is_terminal()
    assert len(resource.history_serializations) == 2
    assert message in resource.status_message
