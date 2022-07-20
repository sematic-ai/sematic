# Sematic
from sematic.types.casting import safe_cast, can_cast_type
from sematic.types.serialization import type_from_json_encodable, type_to_json_encodable


def test_safe_cast():
    assert safe_cast(None, type(None)) == (None, None)
    assert safe_cast(42, type(None)) == (None, "Cannot cast 42 to <class 'NoneType'>")


def test_can_cast_type():
    assert can_cast_type(type(None), type(None)) == (True, None)
    assert can_cast_type(int, type(None)) == (
        False,
        "<class 'int'> cannot cast to <class 'NoneType'>",
    )


def test_type_to_json_encodable():
    assert type_to_json_encodable(type(None)) == {
        "type": ("builtin", "NoneType", {}),
        "registry": {"NoneType": []},
    }


def test_type_from_json_encodable():
    json_encodable = type_to_json_encodable(type(None))
    assert type_from_json_encodable(json_encodable) is type(None)  # noqa: E721
