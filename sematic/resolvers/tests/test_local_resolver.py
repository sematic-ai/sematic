# Standard library
from typing import List

# Third-party
import pytest

# Sematic
from sematic.abstract_future import AbstractFuture, FutureState
from sematic.api.tests.fixtures import (  # noqa: F401
    mock_no_auth,
    test_client,
    mock_requests,
)
from sematic.calculator import func
from sematic.db.models.edge import Edge
from sematic.db.models.factories import make_artifact
from sematic.resolvers.local_resolver import LocalResolver
from sematic.db.tests.fixtures import test_db, pg_mock  # noqa: F401
from sematic.db.queries import get_root_graph


@func
def add(a: float, b: float) -> float:
    return a + b


@func
def add3(a: float, b: float, c: float) -> float:
    return add(add(a, b), c)


@func
def pipeline(a: float, b: float) -> float:
    c = add(a, b)
    d = add3(a, b, c)
    return add(c, d)


@mock_no_auth
def test_single_function(test_db, mock_requests):  # noqa: F811
    future = add(1, 2)

    result = future.set(name="AAA").resolve(LocalResolver())

    assert result == 3

    runs, artifacts, edges = get_root_graph(future.id)

    assert len(runs) == 1
    assert len(artifacts) == 3
    assert len(edges) == 3

    artifact_a = make_artifact(1.0, float)
    artifact_b = make_artifact(2.0, float)
    artifact_output = make_artifact(3.0, float)

    assert set(edges) == {
        Edge(
            source_run_id=None,
            destination_run_id=future.id,
            destination_name="a",
            parent_id=None,
            artifact_id=artifact_a.id,
        ),
        Edge(
            source_run_id=None,
            destination_run_id=future.id,
            destination_name="b",
            parent_id=None,
            artifact_id=artifact_b.id,
        ),
        Edge(
            source_run_id=future.id,
            destination_run_id=None,
            destination_name=None,
            parent_id=None,
            artifact_id=artifact_output.id,
        ),
    }


@func
def add_add_add(a: float, b: float) -> float:
    aa = add(a, b)
    bb = add(a, aa)
    return add(bb, aa)


@mock_no_auth
def test_add_add(test_db, mock_requests):  # noqa: F811
    future = add_add_add(1, 2)

    result = future.resolve(LocalResolver())

    assert result == 7

    runs, artifacts, edges = get_root_graph(future.id)

    assert len(runs) == 4
    assert len(artifacts) == 5
    assert len(edges) == 10


@mock_no_auth
def test_pipeline(test_db, mock_requests):  # noqa: F811
    future = pipeline(3, 5)

    result = future.resolve(LocalResolver())

    assert result == 24
    assert isinstance(result, float)
    assert future.state == FutureState.RESOLVED

    runs, artifacts, edges = get_root_graph(future.id)

    assert len(runs) == 6
    assert len(artifacts) == 5
    assert len(edges) == 16


@mock_no_auth
def test_failure(test_db, mock_requests):  # noqa: F811
    class CustomException(Exception):
        pass

    @func
    def failure(a: None):
        raise CustomException("some message")

    @func
    def success():
        return

    @func
    def pipeline():
        return failure(success())

    resolver = LocalResolver()

    with pytest.raises(CustomException, match="some message"):
        pipeline().resolve(resolver)

    expected_states = dict(
        pipeline=FutureState.NESTED_FAILED,
        success=FutureState.RESOLVED,
        failure=FutureState.FAILED,
    )

    for future in resolver._futures:
        assert future.state == expected_states[future.calculator.__name__]


class DBStateMachineTestResolver(LocalResolver):
    def _future_will_schedule(self, future) -> None:
        super()._future_will_schedule(future)

        run = self._get_run(future.id)

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

        for name, value in future.kwargs.items():
            source_run_id = None
            if isinstance(value, AbstractFuture):
                source_run_id = value.id

            edge = self._get_input_edge(future.id, name)
            assert edge is not None
            assert edge.source_run_id == source_run_id
            assert edge.destination_run_id == future.id
            assert edge.destination_name == name

        output_edges = self._get_output_edges(future.id)

        assert len(output_edges) > 0
        assert all(edge.source_run_id == future.id for edge in output_edges)
        assert all(edge.source_name is None for edge in output_edges)
        assert (
            len(output_edges) == 1
            or all(edge.destination_run_id is not None for edge in output_edges)
            or all(edge.parent_id is not None for edge in output_edges)
        )

    def _future_did_run(self, future) -> None:
        super()._future_did_run(future)

        run = self._get_run(future.id)

        assert run.id == future.id
        assert run.future_state == FutureState.RAN.value

        assert run.ended_at is not None

        output_edges = self._get_output_edges(future.id)

        assert len(output_edges) > 0
        assert all(edge.artifact_id is None for edge in output_edges)

    def _future_did_resolve(self, future) -> None:
        super()._future_did_resolve(future)

        run = self._get_run(future.id)

        assert run.id == future.id
        assert run.future_state == FutureState.RESOLVED.value

        assert run.resolved_at is not None

        output_edges = self._get_output_edges(future.id)

        assert len(output_edges) > 0
        assert all(edge.artifact_id is not None for edge in output_edges)

    def _future_did_fail(self, failed_future) -> None:
        super()._future_did_fail(failed_future)

        run = self._get_run(failed_future.id)

        assert run.id == failed_future.id

        if (
            failed_future.nested_future is not None
            and failed_future.nested_future.state
            in (FutureState.FAILED.value, FutureState.NESTED_FAILED.value)
        ):
            assert run.future_state == FutureState.NESTED_FAILED.value
        else:
            assert run.future_state == FutureState.FAILED.value

        output_edges = self._get_output_edges(failed_future.id)

        assert len(output_edges) > 0
        assert all(edge.artifact_id is None for edge in output_edges)


@mock_no_auth
def test_db_state_machine(test_db, mock_requests):  # noqa: F811
    pipeline(1, 2).resolve(DBStateMachineTestResolver())


@mock_no_auth
def test_list_conversion(test_db, mock_requests):  # noqa: F811
    @func
    def alist(a: float, b: float) -> List[float]:
        return [add(a, b), add(a, b)]

    assert alist(1, 2).resolve() == [3, 3]
