# Third-party
import pytest

# Glow
from glow.abstract_future import FutureState
from glow.calculator import calculator
from glow.db.tests.fixtures import test_db  # noqa: F401
from glow.db.queries import (
    count_runs,
    get_run,
    get_run_input_artifacts,
    get_run_output_artifact,
)
from glow.resolvers.offline_resolver import OfflineResolver


# Testing mypy compliance
@calculator
def add_int(a: int, b: int) -> int:
    return a + b


@calculator
def add(a: float, b: float) -> float:
    return a + b


@calculator
def add3(a: float, b: float, c: float) -> float:
    return add(add(a, b), c)


@calculator
def pipeline(a: float, b: float) -> float:
    c = add(a, b)
    d = add3(a, b, c)
    return add(c, d)


def test_single_calculator(test_db):  # noqa: F811
    future = add(1, 2)
    assert future.resolve(OfflineResolver()) == 3
    assert future.state == FutureState.RESOLVED
    assert count_runs() == 1

    input_artifacts = get_run_input_artifacts(future.id)
    assert set(input_artifacts) == {"a", "b"}
    assert input_artifacts["a"].json_summary == "1.0"
    assert input_artifacts["b"].json_summary == "2.0"

    output_artifact = get_run_output_artifact(future.id)
    assert output_artifact.json_summary == "3.0"


def test_local_resolver(test_db):  # noqa: F811
    future = pipeline(3, 5)

    result = future.resolve(OfflineResolver())

    assert result == 24
    assert isinstance(result, float)
    assert future.state == FutureState.RESOLVED

    assert count_runs() == 6


def test_failure(test_db):  # noqa: F811
    class CustomException(Exception):
        pass

    @calculator
    def failure(a: None):
        raise CustomException("some message")

    @calculator
    def success():
        return

    @calculator
    def pipeline():
        return failure(success())

    resolver = OfflineResolver()

    with pytest.raises(CustomException, match="some message"):
        pipeline().resolve(resolver)

    expected_states = dict(
        pipeline=FutureState.NESTED_FAILED,
        success=FutureState.RESOLVED,
        failure=FutureState.FAILED,
    )

    for future in resolver._futures:
        assert future.state == expected_states[future.calculator.__name__]


class DBStateMachineTestResolver(OfflineResolver):
    def _future_will_schedule(self, future) -> None:
        super()._future_will_schedule(future)

        run = get_run(future.id)

        assert run.id == future.id
        assert run.future_state == FutureState.SCHEDULED.value
        assert run.name == future.calculator.__name__
        assert run.calculator_path == "{}.{}".format(
            future.calculator.__module__, future.calculator.__name__
        )
        assert run.parent_id == (
            future.parent_future.id if future.parent_future is not None else None
        )
        assert run.started_at is not None

    def _future_did_run(self, future) -> None:
        super()._future_did_run(future)

        run = get_run(future.id)

        assert run.id == future.id
        assert run.future_state == FutureState.RAN.value

        assert run.ended_at is not None

    def _future_did_resolve(self, future) -> None:
        super()._future_did_resolve(future)

        run = get_run(future.id)

        assert run.id == future.id
        assert run.future_state == FutureState.RESOLVED.value

        assert run.resolved_at is not None

    def _future_did_fail(self, failed_future) -> None:
        super()._future_did_fail(failed_future)

        run = get_run(failed_future.id)

        assert run.id == failed_future.id

        if (
            failed_future.nested_future is not None
            and failed_future.nested_future.state
            in (FutureState.FAILED.value, FutureState.NESTED_FAILED.value)
        ):
            assert run.future_state == FutureState.NESTED_FAILED.value
        else:
            assert run.future_state == FutureState.FAILED.value


def test_db_state_machine(test_db):  # noqa: F811
    pipeline(1, 2).resolve(DBStateMachineTestResolver())
