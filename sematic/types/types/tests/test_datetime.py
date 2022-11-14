# Standard Library
from datetime import datetime

# Third-party
import pytest

# Sematic
from sematic.types.serialization import (
    get_json_encodable_summary,
    value_from_json_encodable,
    value_to_json_encodable,
)


def test_dict_summary():
    date = datetime.now()
    summary = get_json_encodable_summary(date, datetime)

    assert summary == date.isoformat()


SERIALIZATION_EXAMPLES = [(datetime.now(), datetime), (datetime.today(), datetime)]


@pytest.mark.parametrize("value, type_", SERIALIZATION_EXAMPLES)
def test_value_serdes(value, type_):
    serialized = value_to_json_encodable(value, type_)
    deserialized = value_from_json_encodable(serialized, type_)
    assert deserialized == value
