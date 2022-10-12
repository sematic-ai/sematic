# Standard Library
from typing import List
from unittest import mock

# Third-party
import pytest

# Sematic
from sematic.abstract_future import AbstractFuture, FutureState
from sematic.api.tests.fixtures import (  # noqa: F401
    mock_no_auth,
    mock_requests,
    test_client,
)
from sematic.calculator import func
from sematic.db.models.edge import Edge
from sematic.db.models.factories import make_artifact
from sematic.db.models.resolution import ResolutionStatus
from sematic.db.queries import get_resolution, get_root_graph, get_run
from sematic.db.tests.fixtures import pg_mock, test_db  # noqa: F401
from sematic.resolvers.local_resolver import LocalResolver
from sematic.retry_settings import RetrySettings
from sematic.tests.fixtures import valid_client_version  # noqa: F401
from sematic.utils.exceptions import ExceptionMetadata


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
@mock.patch("socketio.Client.connect")
def test_single_function(
    mock_socketio, test_db, mock_requests, valid_client_version  # noqa: F811
):
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
@mock.patch("socketio.Client.connect")
def test_add_add(
    mock_socketio, test_db, mock_requests, valid_client_version  # noqa: F811
):
    future = add_add_add(1, 2)

    result = future.resolve(LocalResolver())

    assert result == 7

    runs, artifacts, edges = get_root_graph(future.id)

    assert len(runs) == 4
    assert len(artifacts) == 5
    assert len(edges) == 10


@mock_no_auth
@mock.patch("socketio.Client.connect")
def test_pipeline(
    mock_socketio, test_db, mock_requests, valid_client_version  # noqa: F811
):
    future = pipeline(3, 5)

    result = future.resolve(LocalResolver())

    assert result == 24
    assert isinstance(result, float)
    assert future.state == FutureState.RESOLVED

    runs, artifacts, edges = get_root_graph(future.id)
    assert get_resolution(future.id).status == ResolutionStatus.COMPLETE.value

    assert len(runs) == 6
    assert len(artifacts) == 5
    assert len(edges) == 16


@mock_no_auth
@mock.patch("socketio.Client.connect")
def test_failure(
    mock_socketio, test_db, mock_requests, valid_client_version  # noqa: F811
):
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

    future = pipeline()
    with pytest.raises(CustomException, match="some message"):
        future.resolve(resolver)

    assert get_resolution(future.id).status == ResolutionStatus.COMPLETE.value
    expected_states = dict(
        pipeline=FutureState.NESTED_FAILED,
        success=FutureState.RESOLVED,
        failure=FutureState.FAILED,
    )

    for future in resolver._futures:
        assert future.state == expected_states[future.calculator.__name__]


@mock_no_auth
@mock.patch("socketio.Client.connect")
def test_resolver_error(
    mock_socketio, test_db, mock_requests, valid_client_version  # noqa: F811
):
    @func
    def add(x: int, y: int) -> int:
        return x + y

    @func
    def pipeline() -> int:
        return add(add(1, 2), add(3, 4))

    resolver = LocalResolver()

    def intentional_fail(*_, **__):
        raise ValueError("some message")

    # Random failure in resolution logic
    resolver._future_did_resolve = intentional_fail

    future = pipeline()
    with pytest.raises(ValueError, match="some message"):
        future.resolve(resolver)

    assert get_resolution(future.id).status == ResolutionStatus.FAILED.value
    assert get_run(future.id).future_state == FutureState.NESTED_FAILED.value
    assert get_run(future.nested_future.id).future_state == FutureState.FAILED.value
    assert (
        get_run(future.nested_future.kwargs["x"].id).future_state
        == FutureState.FAILED.value
    )
    assert (
        get_run(future.nested_future.kwargs["y"].id).future_state
        == FutureState.FAILED.value
    )


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

        assert run.future_state == failed_future.state

        output_edges = self._get_output_edges(failed_future.id)

        assert len(output_edges) > 0
        assert all(edge.artifact_id is None for edge in output_edges)


@mock_no_auth
@mock.patch("socketio.Client.connect")
def test_db_state_machine(
    mock_socketio, test_db, mock_requests, valid_client_version  # noqa: F811
):
    pipeline(1, 2).resolve(DBStateMachineTestResolver())


@mock_no_auth
@mock.patch("socketio.Client.connect")
def test_list_conversion(
    mock_socketio, test_db, mock_requests, valid_client_version  # noqa: F811
):
    @func
    def alist(a: float, b: float) -> List[float]:
        return [add(a, b), add(a, b)]

    assert alist(1, 2).resolve() == [3, 3]


@mock_no_auth
@mock.patch("socketio.Client.connect")
def test_exceptions(mock_socketio, mock_requests, valid_client_version):  # noqa: F811
    @func
    def fail():
        raise Exception("FAIL!")

    @func
    def pipeline():
        return fail()

    future = pipeline()

    with pytest.raises(Exception, match="FAIL!"):
        future.resolve()

    runs, _, _ = get_root_graph(future.id)

    runs_by_id = {run.id: run for run in runs}

    assert runs_by_id[future.id].future_state == FutureState.NESTED_FAILED.value
    assert runs_by_id[future.id].exception == ExceptionMetadata(
        repr="Failed because the child run failed",
        name="Exception",
        module="builtins",
    )

    assert runs_by_id[future.nested_future.id].future_state == FutureState.FAILED.value
    assert "FAIL!" in runs_by_id[future.nested_future.id].exception.repr


_tried = 0


class SomeException(Exception):
    pass


@func(retry=RetrySettings(exceptions=(SomeException,), retries=3))
def try_three_times():
    global _tried
    _tried += 1
    raise SomeException()


@mock_no_auth
@mock.patch("socketio.Client.connect")
def test_retry(
    mock_socketio, test_db, mock_requests, valid_client_version  # noqa: F811
):
    future = try_three_times()
    try:
        future.resolve(LocalResolver())
    except SomeException:
        pass
    else:
        assert False

    assert future.props.retry_settings.retry_count == 3
    assert future.state == FutureState.FAILED
    assert _tried == 4
