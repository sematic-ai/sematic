# Standard Library
from typing import Optional, Tuple

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


@pytest.mark.parametrize(
    "value, type_, expected_value, expected_error",
    (
        ((42, "foo"), Tuple[float, str], (42, "foo"), None),
        ([42, "foo"], Tuple[float, str], (42, "foo"), None),
        (
            [42, 43],
            Tuple[int, ...],
            None,
            "Sematic does not support Ellipsis in Tuples yet (...)",
        ),
        ((42,), Tuple[float, str], None, "Expected 2 elements, got 1: (42,)"),
        (
            ("foo",),
            Tuple[float],
            None,
            "Cannot cast ('foo',) to typing.Tuple[float]: Cannot cast 'foo' to <class 'float'>",  # noqa: E501
        ),
    ),
)
def test_tuple(value, type_, expected_value, expected_error):
    cast_value, error = safe_cast(value, type_)

    assert error == expected_error
    assert cast_value == expected_value


def test_summary():
    summary, blobs = get_json_encodable_summary(("foo", 42), Tuple[str, float])

    assert summary == ["foo", 42]
    assert blobs == {}


def test_type_from_json_encodable():
    json_encodable = type_to_json_encodable(Tuple[float, str])
    type_ = type_from_json_encodable(json_encodable)
    assert type_ is Tuple[float, str]


@pytest.mark.parametrize(
    "value, type_",
    (
        ((42, "foo"), Tuple[float, str]),
        (("foo", "bar"), Tuple[str, Optional[str]]),
        (("foo", None), Tuple[str, Optional[str]]),
    ),
)
def test_serdes(value, type_):
    serialized = value_to_json_encodable(value, type_)
    deserialized = value_from_json_encodable(serialized, type_)
    assert value == deserialized
