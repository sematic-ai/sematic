# Standard Library
import hashlib
import re
from dataclasses import asdict, dataclass, field
from typing import Dict, List

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
from sematic.types.types.dataclass import fromdict
from sematic.types.types.image import Image


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


@dataclass
class BadDictField:
    bad_dict_field: dict


@dataclass(frozen=True)
class SimplySerializable:
    primitive: int
    other_dataclass: D
    list_field: List[A]
    dict_field: Dict[int, A]
    non_initing: int = field(init=False, default=42)


@dataclass(frozen=True)
class SimplySerializableModified:
    # we add new_field and remove other_dataclass
    primitive: int
    list_field: List[A]
    dict_field: Dict[int, A]
    non_initing: int = field(init=False, default=42)
    new_field: int = 43


class NormalClass:
    pass


@dataclass
class ListOfNormalClassField:
    field: List[NormalClass]


@pytest.mark.parametrize(
    "from_type, to_type, expected_can_cast, expected_error",
    (
        (A, A, True, None),
        (B, A, True, None),
        (
            A,
            B,
            False,
            r"Cannot cast .*test_dataclass.A'.* to .*test_dataclass.B'.*: missing fields: {'b'}",  # noqa: E501
        ),
        (
            A,
            C,
            False,
            r"Cannot cast .*test_dataclass.A'.* to .*test_dataclass.C'.*: field 'a' cannot cast: .*'int'.* cannot cast to str",  # noqa: E501
        ),
        (
            C,
            A,
            False,
            r"Cannot cast .*test_dataclass.C'.* to .*test_dataclass.A'.*: field 'a' cannot cast: Cannot cast .*'str'.* to int",  # noqa: E501
        ),
        (D, A, True, None),
        (
            A,
            D,
            False,
            r"Cannot cast .*test_dataclass.A'.* to .*test_dataclass.D'.*: missing fields: {'d'}",  # noqa: E501
        ),
    ),
)
def test_can_cast_type(from_type, to_type, expected_can_cast, expected_error):
    can_cast, error = can_cast_type(from_type, to_type)
    assert can_cast is expected_can_cast
    if expected_error is None:
        assert error is None
    else:
        assert re.match(expected_error, error)


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
            r"Cannot cast A\(a=1\) to .*test_dataclass.B.*: Field 'b' is missing",  # noqa: E501
        ),
        (C(a="1"), A, A, A(a=1), None),
        (
            C(a="abc"),
            A,
            None,
            None,
            r"Cannot cast field 'a' of C.a='abc'. to .*"
            r"test_dataclass.A.*: "
            r"Cannot cast 'abc' to .*int.*",  # noqa: E501
        ),
        (
            MyFrozenDataclass("some value"),
            MyFrozenDataclass,
            MyFrozenDataclass,
            MyFrozenDataclass("some value"),
            None,
        ),
        (
            BadDictField({"foo": "bar"}),
            BadDictField,
            BadDictField,
            None,
            r"Cannot cast field 'bad_dict_field' of "
            r"BadDictField\(bad_dict_field={'foo': 'bar'}\) to .*"
            r"test_dataclass.BadDictField.*:"
            r" Type 'dict' is not a valid Sematic type: dict must be parametrized "
            r".*dict\[\.\.\.\] instead of dict.*",
        ),
    ),
)
def test_safe_cast(value, type_, expected_type, expected_value, expected_error):
    cast_value, error = safe_cast(value, type_)
    if expected_error is None:
        assert isinstance(cast_value, expected_type)
        assert cast_value == expected_value

    if expected_error is None:
        assert error is None
    else:
        assert re.match(expected_error, error)


def test_type_to_json_encodable():
    result = type_to_json_encodable(A)
    assert result == {
        "type": (
            "dataclass",
            "A",
            {
                "import_path": A.__module__,
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
            {"import_path": DD.__module__},
        ),
        "registry": {
            "DD": [
                (
                    "dataclass",
                    "D",
                    {
                        "import_path": DD.__module__,
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
                        "import_path": D.__module__,
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


@dataclass
class OldVersionOfDataclass:
    field1: int


@dataclass
class NewVersionOfDataclass:
    """Simulate if OldVersionOfDataclass was different in a newer commit of the code."""

    field1: int
    field2: int = 42


def test_backwards_compatibility():
    encodable = value_to_json_encodable(
        OldVersionOfDataclass(field1=1), OldVersionOfDataclass
    )

    # In reality, if there was a new version of code trying to deserialize a value
    # written with the old version, the root_type would not be changed. But since
    # we have only one commit of code to work with in the test, we have to emulate
    # a changed class definition by using a different class in the same commit.
    encodable["root_type"] = type_to_json_encodable(NewVersionOfDataclass)
    decoded = value_from_json_encodable(encodable, NewVersionOfDataclass)
    assert decoded == NewVersionOfDataclass(field1=1, field2=42)


@dataclass
class ClassWithImage:
    foo: Image
    bar: Image


def test_summary_with_blobs():
    bytes_ = b"foobar"
    image = Image(bytes=bytes_)

    blob_id = hashlib.sha1(bytes_).hexdigest()

    dc = ClassWithImage(foo=image, bar=image)

    summary, blobs = get_json_encodable_summary(dc, ClassWithImage)

    assert summary["values"] == {
        "foo": {"mime_type": "text/plain", "bytes": {"blob": blob_id}},
        "bar": {"mime_type": "text/plain", "bytes": {"blob": blob_id}},
    }

    assert blobs == {blob_id: bytes_}


def test_fromdict():
    simply_serializable_in = SimplySerializable(
        primitive=1,
        other_dataclass=D(a=2, d=3.5),
        list_field=[A(4), A(5)],
        dict_field={6: A(6), 7: A(7)},
    )
    serialized = asdict(simply_serializable_in)

    assert serialized == {
        "primitive": 1,
        "other_dataclass": {"a": 2, "d": 3.5},
        "list_field": [{"a": 4}, {"a": 5}],
        "dict_field": {6: {"a": 6}, 7: {"a": 7}},
        "non_initing": 42,
    }

    simply_serializable_out = fromdict(SimplySerializable, serialized)
    assert simply_serializable_in == simply_serializable_out


def test_fromdict_backwards_compatibility():
    simply_serializable_in = SimplySerializable(
        primitive=1,
        other_dataclass=D(a=2, d=3.5),
        list_field=[A(4), A(5)],
        dict_field={6: A(6), 7: A(7)},
    )
    serialized = asdict(simply_serializable_in)

    # emulate us adding a new field and removing an existing one,
    # then trying to deserialize something that was serailized
    # with the original class:
    modified_out = fromdict(SimplySerializableModified, serialized)

    expected_modified = SimplySerializableModified(
        primitive=1,
        list_field=[A(4), A(5)],
        dict_field={6: A(6), 7: A(7)},
        new_field=43,
    )

    assert modified_out == expected_modified


def test_fromdict_bad_type():
    with pytest.raises(TypeError):
        fromdict(NormalClass, {})


def test_fromdict_bad_dict():
    with pytest.raises(TypeError):
        fromdict(SimplySerializable, dict(random="field"))
