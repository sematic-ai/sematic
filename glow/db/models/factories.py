"""
Functions to generate models.
"""
# Standard library
import typing
import hashlib
import json

# Glow
from glow.abstract_future import AbstractFuture
from glow.db.models.artifact import Artifact
from glow.db.models.run import Run
from glow.types.serialization import (
    value_to_json_encodable,
    type_to_json_encodable,
    get_json_summary,
)


def make_run_from_future(future: AbstractFuture) -> Run:
    run = Run(
        id=future.id,
        future_state=future.state.value,
        name=future.name,
        calculator_path="{}.{}".format(
            future.calculator.__module__, future.calculator.__name__
        ),
        parent_id=(
            future.parent_future.id if future.parent_future is not None else None
        ),
        description=future.calculator.__doc__,
        tags=future.tags,
    )

    return run


def make_artifact(value: typing.Any, type_: typing.Any) -> Artifact:
    artifact = Artifact(
        id=_get_value_sha1_digest(value, type_),
        json_summary=get_json_summary(value, type_),
    )

    return artifact


def _get_value_sha1_digest(value: typing.Any, type_: typing.Any) -> str:
    payload = {
        "value": value_to_json_encodable(value, type_),
        "type": type_to_json_encodable(type_),
        # Should there be some sort of type versioning concept here?
    }

    binary = json.dumps(payload, sort_keys=True).encode("utf-8")

    sha1_digest = hashlib.sha1(binary)

    return sha1_digest.hexdigest()
