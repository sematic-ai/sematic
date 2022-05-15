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
from glow.types.serialization import to_binary


def make_run_from_future(future: AbstractFuture) -> Run:
    run = Run(
        id=future.id,
        future_state=future.state.value,
        # todo(@neutralino1): replace with future name
        name=future.calculator.__name__,
        calculator_path="{}.{}".format(
            future.calculator.__module__, future.calculator.__name__
        ),
        parent_id=(
            future.parent_future.id if future.parent_future is not None else None
        ),
    )

    return run


def make_artifact(value: typing.Any, type_: typing.Any) -> Artifact:
    binary_serialization = to_binary(value, type_)

    sha1_digest = hashlib.sha1(binary_serialization).hexdigest()

    artifact = Artifact(
        id=sha1_digest,
        # Replace with registered function
        json_summary=json.dumps(value),
    )

    return artifact
