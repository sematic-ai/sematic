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


def test_str_digest():
    assert get_str_sha1_digest(str(1)) == HASH_1
    assert get_str_sha1_digest("a") == HASH_A


def test_value_and_type_digest():
    value = {"a": 1}
    type_ = Dict[str, int]

    type_serialization_1 = type_to_json_encodable(type_)
    value_serialization_1 = value_to_json_encodable(value, type_)
    json_summary_1, _ = get_json_encodable_summary(value, type_)

    actual_1 = get_value_and_type_sha1_digest(
        value_serialization_1, type_serialization_1, json_summary_1
    )

    type_serialization_2 = type_to_json_encodable(type_)
    value_serialization_2 = value_to_json_encodable(value, type_)
    json_summary_2, _ = get_json_encodable_summary(value, type_)

    actual_2 = get_value_and_type_sha1_digest(
        value_serialization_2, type_serialization_2, json_summary_2
    )

    assert actual_1 == actual_2
