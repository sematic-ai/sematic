# Standard Library
from typing import Dict, Union

# Third-party
import pytest

# Sematic
from sematic.types.serialization import (
    value_from_json_encodable,
    value_to_json_encodable,
)


SERIALIZATION_EXAMPLES = [
    (1, Union[int, None]),
    (None, Union[int, None]),
    (1, Union[int, float]),
    ("1", Union[int, str]),
    ("1", Union[str, int]),
    (1, Union[int, str]),
    (1, Union[str, int]),
    ({1: "a", 2: "b"}, Union[Dict[int, str], None]),
]


@pytest.mark.parametrize("value, type_", SERIALIZATION_EXAMPLES)
def test_value_serdes(value, type_):
    serialized = value_to_json_encodable(value, type_)
    deserialized = value_from_json_encodable(serialized, type_)
    assert deserialized == value
