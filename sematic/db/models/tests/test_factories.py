# Standard library
import hashlib
import json

import pytest

# Sematic
from sematic.abstract_future import FutureState
from sematic.calculator import func
from sematic.db.models.factories import (
    get_artifact_value,
    make_run_from_future,
    make_artifact,
    _make_artifact_storage_key,
)
from sematic.types.serialization import (
    get_json_encodable_summary,
    value_to_json_encodable,
    type_to_json_encodable,
)
from sematic.tests.fixtures import test_storage  # noqa: F401
import sematic.storage as storage


@func
def f():
    """
    An informative docstring.
    """
    pass  # Some note


def test_make_run_from_future():
    future = f()
    parent_future = f()
    future.parent_future = parent_future
    run = make_run_from_future(future)

    assert run.id == future.id
    assert run.future_state == FutureState.CREATED.value
    assert run.calculator_path == "sematic.db.models.tests.test_factories.f"
    assert run.name == "f"
    assert run.parent_id == parent_future.id
    assert run.description == "An informative docstring."
    assert (
        run.source_code
        == """@func
def f():
    \"\"\"
    An informative docstring.
    \"\"\"
    pass  # Some note
"""
    )


def test_make_artifact():
    artifact = make_artifact(42, int)

    value_serialization = value_to_json_encodable(42, int)
    type_serialization = type_to_json_encodable(int)
    json_summary = get_json_encodable_summary(42, int)

    payload = {
        "value": value_serialization,
        "type": type_serialization,
        "summary": json_summary,
    }

    sha1 = hashlib.sha1(json.dumps(payload, sort_keys=True).encode("utf-8"))

    assert artifact.id == sha1.hexdigest()
    assert artifact.json_summary == json.dumps(json_summary, sort_keys=True)
    assert artifact.type_serialization == json.dumps(type_serialization, sort_keys=True)


@pytest.mark.parametrize(
    "value, expected_value",
    (
        (float("nan"), "NaN"),
        (float("Infinity"), "Infinity"),
        (float("-Infinity"), "-Infinity"),
    ),
)
def test_make_artifact_special_floats(value, expected_value):
    artifact = make_artifact(value, float)

    assert json.loads(artifact.json_summary) == expected_value


def test_make_artifact_store_true(test_storage):  # noqa: F811
    artifact = make_artifact(42, int, store=True)

    storage_key = _make_artifact_storage_key(artifact)

    assert storage.get(storage_key) == "42".encode("utf-8")


def test_make_artifact_store_false(test_storage):  # noqa: F811
    artifact = make_artifact(42, int, store=False)

    storage_key = _make_artifact_storage_key(artifact)

    with pytest.raises(KeyError):
        storage.get(storage_key)


def test_get_artifact_value(test_storage):  # noqa: F811
    artifact = make_artifact(42, int, store=True)

    value = get_artifact_value(artifact)

    assert value == 42
    assert isinstance(value, int)
