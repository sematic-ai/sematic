# Standard Library
from typing import Dict, Union

# Third-party
import pytest

# Sematic
from sematic.types.casting import safe_cast
from sematic.types.serialization import (
    get_json_encodable_summary,
    type_from_json_encodable,
    type_to_json_encodable,
    value_from_json_encodable,
    value_to_json_encodable,
)


class StringSubclass(str):
    pass


@pytest.mark.parametrize(
    "value, type_, expected_value, expected_error",
    (
        (dict(a=1), Dict[str, float], dict(a=1), None),
        (dict(a=1, b="foo"), Dict[str, Union[float, str]], dict(a=1, b="foo"), None),
        (dict(), Dict[str, float], dict(), None),
        (
            dict(a="foo"),
            Dict[str, int],
            None,
            "Cannot cast 'foo' to value type: Cannot cast 'foo' to <class 'int'>",
        ),
    ),
)
def test_dict(value, type_, expected_value, expected_error):
    cast_value, error = safe_cast(value, type_)

    assert error == expected_error
    assert cast_value == expected_value


def test_dict_summary():
    summary = get_json_encodable_summary(dict(a=123), Dict[str, int])

    assert summary == [("a", 123)]


@pytest.mark.parametrize("type_", (Dict[str, int],))
def test_type_from_json_encodable(type_):
    json_encodable = type_to_json_encodable(type_)
    assert type_from_json_encodable(json_encodable) is type_


SERIALIZATION_EXAMPLES = [
    (dict(a=1.0), Dict[str, float], None),
    (dict(a="b"), Dict[str, str], None),
    ({1: "a", 2: "b"}, Dict[int, str], None),
    ({1: "a", 2: "b"}, Union[Dict[int, str], None], None),
    (
        {1: "a", 2: StringSubclass("b")},
        Dict[int, str],
        lambda deserialized: isinstance(deserialized[2], StringSubclass),
    ),
]


@pytest.mark.parametrize("value, type_, deserialized_check", SERIALIZATION_EXAMPLES)
def test_value_serdes(value, type_, deserialized_check):
    serialized = value_to_json_encodable(value, type_)
    deserialized = value_from_json_encodable(serialized, type_)
    assert deserialized == value
    if deserialized_check is not None:
        assert deserialized_check(deserialized)
