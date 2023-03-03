# Standard Library
from typing import Dict

# Sematic
from sematic.types.serialization import (
    get_json_encodable_summary,
    type_to_json_encodable,
    value_to_json_encodable,
)
from sematic.utils.hashing import get_str_sha1_digest, get_value_and_type_sha1_digest

HASH_1 = "356a192b7913b04c54574d18c28d46e6395428ab"
HASH_A = "86f7e437faa5a7fce15d1ddcb9eaeaea377667b8"
HASH_VALUE_AND_TYPE = "cb7a7ae1a4d8ec92524ce5eee7aa1570b0ca5799"


def test_str_digest():
    assert get_str_sha1_digest(str(1)) == HASH_1
    assert get_str_sha1_digest("a") == HASH_A


def test_value_and_type_digest():
    value = {"a": 1}
    type_ = Dict[str, int]

    type_serialization = type_to_json_encodable(type_)
    value_serialization = value_to_json_encodable(value, type_)
    json_summary, _ = get_json_encodable_summary(value, type_)

    actual = get_value_and_type_sha1_digest(
        value_serialization, type_serialization, json_summary
    )

    assert actual == HASH_VALUE_AND_TYPE
