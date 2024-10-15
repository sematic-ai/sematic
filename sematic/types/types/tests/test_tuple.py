# Standard Library
import hashlib
from typing import Optional, Tuple

# Third-party
import pytest

# Sematic
from sematic.types.casting import can_cast_type, safe_cast
from sematic.types.serialization import (
    get_json_encodable_summary,
    type_from_json_encodable,
    type_to_json_encodable,
    value_from_json_encodable,
    value_to_json_encodable,
)
from sematic.types.types.image import Image


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


@pytest.mark.parametrize(
    "from_type, to_type, expected_error",
    (
        (Tuple[float, int], Tuple[float, int], None),
        (Tuple[float, int], Tuple[float, float], None),
        (Tuple[int, str], Tuple[float, str], None),
        (Tuple[int, str], int, "Cannot cast typing.Tuple[int, str] to int"),
        (
            Tuple[int, str],
            Tuple[int, str, int],
            "Can't cast typing.Tuple[int, str] to typing.Tuple[int, str, int]: "
            "they have different arities (2 vs 3)",
        ),
        (
            Tuple[int, str],
            Tuple[int, int],
            "Can't cast typing.Tuple[int, str] to typing.Tuple[int, int]:: "
            "Cannot cast <class 'str'> to int",
        ),
    ),
)
def test_can_cast_tuple(from_type, to_type, expected_error):
    can_cast, error = can_cast_type(from_type, to_type)
    if expected_error is None:
        assert error is None
        assert can_cast
    else:
        assert not can_cast
    assert error == expected_error


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


def test_summary_blobs():
    bytes_ = b"foo"
    image = Image(bytes=bytes_)
    blob_id = hashlib.sha1(bytes_).hexdigest()

    summary, blobs = get_json_encodable_summary((image, image), Tuple[Image, Image])

    assert summary == [{"mime_type": "text/plain", "bytes": {"blob": blob_id}}] * 2
    assert blobs == {blob_id: bytes_}
