# Standard Library
from dataclasses import dataclass

# Third-party
import pytest

# Sematic
from sematic.types.casting import can_cast_type, safe_cast
from sematic.types.serialization import (
    type_from_json_encodable,
    type_to_json_encodable,
    value_from_json_encodable,
    value_to_json_encodable,
)


@dataclass
class A:
    a: int


@dataclass
class B:
    a: float
    b: str


@dataclass
class C:
    a: str


@dataclass
class D(A):
    d: float


@dataclass
class E:
    a: float


@dataclass
class MyFrozenDataclass:
    field: str


@pytest.mark.parametrize(
    "from_type, to_type, expected_can_cast, expected_error",
    (
        (A, A, True, None),
        (B, A, True, None),
        (
            A,
            B,
            False,
            "Cannot cast <class 'sematic.types.types.tests.test_dataclass.A'> to <class 'sematic.types.types.tests.test_dataclass.B'>: missing fields: {'b'}",  # noqa: E501
        ),
        (
            A,
            C,
            False,
            "Cannot cast <class 'sematic.types.types.tests.test_dataclass.A'> to <class 'sematic.types.types.tests.test_dataclass.C'>: field 'a' cannot cast: <class 'int'> cannot cast to str",  # noqa: E501
        ),
        (
            C,
            A,
            False,
            "Cannot cast <class 'sematic.types.types.tests.test_dataclass.C'> to <class 'sematic.types.types.tests.test_dataclass.A'>: field 'a' cannot cast: Cannot cast <class 'str'> to int",  # noqa: E501
        ),
        (D, A, True, None),
        (
            A,
            D,
            False,
            "Cannot cast <class 'sematic.types.types.tests.test_dataclass.A'> to <class 'sematic.types.types.tests.test_dataclass.D'>: missing fields: {'d'}",  # noqa: E501
        ),
    ),
)
def test_can_cast_type(from_type, to_type, expected_can_cast, expected_error):
    can_cast, error = can_cast_type(from_type, to_type)
    assert can_cast is expected_can_cast
    assert error == expected_error


@pytest.mark.parametrize(
    "value, type_, expected_type, expected_value, expected_error",
    (
        (A(a=1), A, A, A(a=1), None),
        (E(a=1.1), A, A, A(a=1), None),
        (D(a=1, d=2.3), A, D, D(a=1, d=2.3), None),
        (dict(a=1), A, A, A(a=1), None),
        (E(a=1.1), A, A, A(a=1), None),
        (B(a=1.1, b="b"), A, A, A(a=1), None),
        (
            A(a=1),
            B,
            None,
            None,
            "Cannot cast A(a=1) to <class 'sematic.types.types.tests.test_dataclass.B'>: Field 'b' is missing",  # noqa: E501
        ),
        (C(a="1"), A, A, A(a=1), None),
        (
            C(a="abc"),
            A,
            None,
            None,
            "Cannot cast C(a='abc') to <class 'sematic.types.types.tests.test_dataclass.A'>: Cannot cast 'abc' to <class 'int'>",  # noqa: E501
        ),
        (
            MyFrozenDataclass("some value"),
            MyFrozenDataclass,
            MyFrozenDataclass,
            MyFrozenDataclass("some value"),
            None,
        ),
    ),
)
def test_safe_cast(value, type_, expected_type, expected_value, expected_error):
    cast_value, error = safe_cast(value, type_)
    if expected_error is None:
        assert isinstance(cast_value, expected_type)
        assert cast_value == expected_value

    assert error == expected_error


def test_type_to_json_encodable():
    assert type_to_json_encodable(A) == {
        "type": (
            "dataclass",
            "A",
            {
                "import_path": "sematic.types.types.tests.test_dataclass",
                "fields": {"a": {"type": ("builtin", "int", {})}},
            },
        ),
        "registry": {"A": [], "int": []},
    }


class DD(D):
    pass


def test_type_to_json_encodable_subclass():
    assert type_to_json_encodable(DD) == {
        "type": (
            "class",
            "DD",
            {"import_path": "sematic.types.types.tests.test_dataclass"},
        ),
        "registry": {
            "DD": [
                (
                    "dataclass",
                    "D",
                    {
                        "import_path": "sematic.types.types.tests.test_dataclass",
                        "fields": {
                            "a": {"type": ("builtin", "int", {})},
                            "d": {"type": ("builtin", "float", {})},
                        },
                    },
                )
            ],
            "D": [
                (
                    "dataclass",
                    "A",
                    {
                        "import_path": "sematic.types.types.tests.test_dataclass",
                        "fields": {"a": {"type": ("builtin", "int", {})}},
                    },
                )
            ],
            "A": [],
            "int": [],
            "float": [],
        },
    }


@dataclass
class F:
    a: A
    b: B
    c: C
    d: D
    e: E
    dd: DD


@pytest.mark.parametrize(
    "type_",
    (A, B, C, D, E, DD, F),
)
def test_type_from_json_encodable(type_):
    json_encodable = type_to_json_encodable(type_)
    assert type_from_json_encodable(json_encodable) is type_


def test_serialization():
    value = F(
        a=A(a=1),
        b=B(a=2.1, b="b"),
        c=C(a="a"),
        d=D(a=3, d=4.5),
        e=E(a=5.6),
        dd=DD(a=7, d=8.9),
    )

    json_encodable = value_to_json_encodable(value, F)

    assert value_from_json_encodable(json_encodable, F) == value

    d = D(a=3, d=4.5)
    json_encodable = value_to_json_encodable(d, A)
    assert value_from_json_encodable(json_encodable, A) == d
