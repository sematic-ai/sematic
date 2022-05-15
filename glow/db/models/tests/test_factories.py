# Standard library
import hashlib

# Glow
from glow.abstract_future import FutureState
from glow.calculator import calculator
from glow.db.models.factories import make_run_from_future, make_artifact
from glow.types.serialization import to_binary


@calculator
def func():
    pass


def test_make_run_from_future():
    future = func()
    parent_future = func()
    future.parent_future = parent_future
    run = make_run_from_future(future)

    assert run.id == future.id
    assert run.future_state == FutureState.CREATED.value
    assert run.calculator_path == "glow.db.models.tests.test_factories.func"
    assert run.name == "func"
    assert run.parent_id == parent_future.id


def test_make_artifact():
    artifact = make_artifact(42, int)

    sha1_digest = hashlib.sha1(to_binary(42, int)).hexdigest()

    assert artifact.id == sha1_digest
    assert artifact.json_summary == "42"
