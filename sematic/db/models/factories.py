"""
Functions to generate models.
"""
# Standard library
import datetime
import typing
import hashlib
import json

# Sematic
from sematic.abstract_future import AbstractFuture
from sematic.db.models.artifact import Artifact
from sematic.db.models.run import Run
from sematic.types.serialization import (
    value_to_json_encodable,
    type_to_json_encodable,
    get_json_encodable_summary,
)


def make_run_from_future(future: AbstractFuture) -> Run:
    run = Run(
        id=future.id,
        future_state=future.state,
        name=future.name,
        calculator_path="{}.{}".format(
            future.calculator.__module__, future.calculator.__name__
        ),
        parent_id=(
            future.parent_future.id if future.parent_future is not None else None
        ),
        description=future.calculator.__doc__,
        tags=future.tags,
        source_code=future.calculator.get_source(),
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow(),
    )

    return run


def make_artifact(value: typing.Any, type_: typing.Any) -> Artifact:
    type_serialization = type_to_json_encodable(type_)
    value_serialization = value_to_json_encodable(value, type_)
    json_summary = get_json_encodable_summary(value, type_)

    artifact = Artifact(
        id=_get_value_sha1_digest(
            value_serialization, type_serialization, json_summary
        ),
        json_summary=_fix_nan_inf(json.dumps(json_summary, sort_keys=True)),
        type_serialization=json.dumps(type_serialization, sort_keys=True),
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow(),
    )

    return artifact


def _get_value_sha1_digest(
    value_serialization: typing.Any,
    type_serialization: typing.Any,
    json_summary: typing.Any,
) -> str:
    payload = {
        "value": value_serialization,
        "type": type_serialization,
        "summary": json_summary,
        # Should there be some sort of type versioning concept here?
    }

    binary = _fix_nan_inf(json.dumps(payload, sort_keys=True)).encode("utf-8")

    sha1_digest = hashlib.sha1(binary)

    return sha1_digest.hexdigest()


def _fix_nan_inf(string: str) -> str:
    """
    Dirty hack to remedy mismatches between ECMAS6 JSON specs and Pythoh JSON
    specs Python respects the JSON5 spec (https://spec.json5.org/) which
    supports NaN, Infinity, and -Infinity as numbers, whereas ECMAS6 does not
    (Unexpected token N in JSON at position) TODO: find a more sustainable
    solution
    """
    return (
        string.replace("NaN", '"NaN"')
        .replace("Infinity", '"Infinity"')
        .replace('-"Infinity"', '"-Infinity"')
    )
