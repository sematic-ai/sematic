# Standard library
import collections
import json
import typing

# Third-party
import pytest

# Glow
from glow.types.casting import safe_cast, can_cast_type
from glow.types.serialization import to_binary, type_to_json_encodable


@pytest.mark.parametrize(
    "type_, value, expected_cast_value, expected_error",
    (
        (typing.List[int], [1, 2, 3], [1, 2, 3], None),
        (typing.List[int], [1.2, 3.4], [1, 3], None),
        (typing.List[float], ["1.2", 3], [1.2, 3], None),
        (
            typing.List[float],
            ["abc"],
            None,
            (
                "Cannot cast ['abc'] to typing.List[float]: "
                "Cannot cast 'abc' to <class 'float'>"
            ),
        ),
    ),
)
def test_safe_cast(type_, value, expected_cast_value, expected_error):
    cast_value, error = safe_cast(value, type_)

    assert cast_value == expected_cast_value
    assert error == expected_error


@pytest.mark.parametrize(
    "from_type, to_type, expected_can_cast, expected_error",
    (
        (typing.List[float], typing.List[int], True, None),
        # Need to implement str casting logic
        # (typing.List[float], typing.List[str], True, None),
        (
            float,
            typing.List[int],
            False,
            "Can't cast <class 'float'> to typing.List[int]: not a subscripted generic",
        ),
        (typing.Tuple[int, float], typing.List[float], True, None),
        (
            typing.Tuple[typing.List[float], typing.List[int]],
            typing.List[typing.List[int]],
            True,
            None,
        ),
    ),
)
def test_can_cast_type(from_type, to_type, expected_can_cast, expected_error):
    can_cast, error = can_cast_type(from_type, to_type)
    assert can_cast is expected_can_cast
    assert error == expected_error


def test_type_to_json_encodable():
    type_ = typing.List[int]

    json_encodable = type_to_json_encodable(type_)

    assert json_encodable == collections.OrderedDict(
        (
            (
                "type",
                ("typing", "list", {"args": [{"type": ("builtins", "int", None)}]}),
            ),
            ("registry", collections.OrderedDict((("int", []), ("list", [])))),
        )
    )


def test_type_to_json_encodable_subclass():
    type_ = typing.List[typing.Optional[typing.Dict[str, typing.Union[int, float]]]]

    json_encodable = type_to_json_encodable(type_)

    print(json_encodable["type"][2]["args"][0])

    assert json_encodable == collections.OrderedDict(
        (
            (
                "type",
                (
                    "typing",
                    "list",
                    {
                        "args": [
                            {
                                "type": (
                                    "typing",
                                    "Union",
                                    {
                                        "args": [
                                            {
                                                "type": (
                                                    "typing",
                                                    "dict",
                                                    {
                                                        "args": [
                                                            {
                                                                "type": (
                                                                    "builtins",
                                                                    "str",
                                                                    None,
                                                                )
                                                            },
                                                            {
                                                                "type": (
                                                                    "typing",
                                                                    "Union",
                                                                    {
                                                                        "args": [
                                                                            {
                                                                                "type": (
                                                                                    "builtins",
                                                                                    "int",
                                                                                    None,
                                                                                ),
                                                                            },
                                                                            {
                                                                                "type": (
                                                                                    "builtins",
                                                                                    "float",
                                                                                    None,
                                                                                ),
                                                                            },
                                                                        ]
                                                                    },
                                                                )
                                                            },
                                                        ]
                                                    },
                                                )
                                            },
                                            {"type": ("builtins", "NoneType", None)},
                                        ]
                                    },
                                )
                            },
                        ]
                    },
                ),
            ),
            (
                "registry",
                collections.OrderedDict(
                    (
                        ("str", []),
                        ("int", []),
                        ("float", []),
                        ("Union", []),
                        ("dict", []),
                        ("NoneType", []),
                        ("list", []),
                    )
                ),
            ),
        )
    )


def test_to_binary():
    type_ = typing.List[int]

    binary = to_binary([1, 2, 3], type_)

    assert binary.decode("utf-8") == "[1, 2, 3]"


# Needs to be defined here intead of inside test_to_binary_arbitrary
# to make sure pickling is deterministic
class A:
    pass


def test_to_binary_arbitrary():

    type_ = typing.List[A]

    binary = to_binary([A(), A()], type_)

    assert json.loads(binary.decode("utf-8")) == [
        "gAWVLQAAAAAAAACMIGdsb3cudHlwZXMudHlwZXMudGVzdHMudGVzdF9saXN0lIwBQZSTlCmBlC4=",  # noqa: E501
        "gAWVLQAAAAAAAACMIGdsb3cudHlwZXMudHlwZXMudGVzdHMudGVzdF9saXN0lIwBQZSTlCmBlC4=",  # noqa: E501
    ]
