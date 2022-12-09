# Standard Library
from collections import defaultdict
from typing import List

# Third-party
import pytest

# Sematic
from sematic.abstract_calculator import CalculatorError
from sematic.abstract_future import AbstractFuture, FutureState
from sematic.api.tests.fixtures import (  # noqa: F401
    mock_auth,
    mock_requests,
    mock_socketio,
    test_client,
)
from sematic.calculator import func
from sematic.db.models.edge import Edge
from sematic.db.models.factories import make_artifact
from sematic.db.models.resolution import ResolutionKind, ResolutionStatus
from sematic.db.queries import get_resolution, get_root_graph, get_run
from sematic.db.tests.fixtures import pg_mock, test_db  # noqa: F401
from sematic.resolvers.local_resolver import LocalResolver
from sematic.resolvers.tests.fixtures import mock_local_resolver_storage  # noqa: F401
from sematic.retry_settings import RetrySettings
from sematic.tests.fixtures import valid_client_version  # noqa: F401
from sematic.utils.exceptions import ExceptionMetadata, ResolutionError


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


def test_single_function(
    mock_local_resolver_storage,  # noqa: F811
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
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


def test_add_add(
    mock_local_resolver_storage,  # noqa: F811
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    future = add_add_add(1, 2)

    result = future.resolve(LocalResolver())

    assert result == 7

    runs, artifacts, edges = get_root_graph(future.id)

    assert len(runs) == 4
    assert len(artifacts) == 5
    assert len(edges) == 10


def test_pipeline(
    mock_local_resolver_storage,  # noqa: F811
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    resolver = CallbackTrackingResolver()
    future = pipeline(3, 5)

    result = future.resolve(resolver)

    assert result == 24
    assert isinstance(result, float)
    assert future.state == FutureState.RESOLVED

    runs, artifacts, edges = get_root_graph(future.id)
    assert get_resolution(future.id).status == ResolutionStatus.COMPLETE.value

    assert len(runs) == 6
    assert len(artifacts) == 5
    assert len(edges) == 16
    pipeline_callbacks = resolver.callback_by_future_id(future.id)
    final_add_callbacks = resolver.callback_by_future_id(future.nested_future.id)
    assert pipeline_callbacks == [
        "_future_did_schedule",
        "_future_did_run",
        "_future_did_resolve",
        "_future_did_terminate",
    ]
    assert final_add_callbacks == [
        "_future_did_schedule",
        "_future_did_resolve",
        "_future_did_terminate",
    ]


def test_failure(
    mock_local_resolver_storage,  # noqa: F811
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
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

    with pytest.raises(ResolutionError, match="some message") as exc_info:
        future.resolve(resolver)

    assert isinstance(exc_info.value.__context__, CalculatorError)
    assert isinstance(exc_info.value.__context__.__context__, CustomException)

    assert get_resolution(future.id).status == ResolutionStatus.FAILED.value
    expected_states = dict(
        pipeline=FutureState.NESTED_FAILED,
        success=FutureState.RESOLVED,
        failure=FutureState.FAILED,
    )

    for future in resolver._futures:
        assert future.state == expected_states[future.calculator.__name__]


def test_resolver_error(
    mock_local_resolver_storage,  # noqa: F811
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
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

    with pytest.raises(ResolutionError, match="some message") as exc_info:
        future.resolve(resolver)

    # this test doesn't really go through the entire Resolver logic due to
    # the custom setting of _future_did_resolve above, so no CalculatorError here
    # TODO: replace with testing logic that goes through the entire tested code logic
    assert isinstance(exc_info.value.__context__, ValueError)

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


class CallbackTrackingResolver(LocalResolver):
    def __init__(self, rerun_from=None, **kwargs):
        super().__init__(rerun_from, **kwargs)
        # list of tuples: (callback name, future, future_state)
        self._callback_invocations = []

    def _future_did_schedule(self, future):
        super()._future_did_schedule(future)
        self._callback_invocations.append(
            ("_future_did_schedule", future, future.state)
        )

    def _future_did_run(self, future):
        super()._future_did_run(future)
        self._callback_invocations.append(("_future_did_run", future, future.state))

    def _future_did_fail(self, future):
        super()._future_did_fail(future)
        self._callback_invocations.append(("_future_did_fail", future, future.state))

    def _future_did_resolve(self, future):
        super()._future_did_resolve(future)
        self._callback_invocations.append(("_future_did_resolve", future, future.state))

    def _future_did_get_marked_for_retry(self, future):
        super()._future_did_get_marked_for_retry(future)
        self._callback_invocations.append(
            ("_future_did_get_marked_for_retry", future, future.state)
        )

    def _future_did_terminate(self, future):
        super()._future_did_terminate(future)
        self._callback_invocations.append(
            ("_future_did_terminate", future, future.state)
        )

    def callback_by_future_id(self, future_id) -> List[str]:
        return [
            callback
            for callback, future, _ in self._callback_invocations
            if future.id == future_id
        ]

    def state_sequence_by_future_id(self, future_id) -> List[FutureState]:
        state_sequence = [
            state
            for _, future, state in self._callback_invocations
            if future.id == future_id
        ]

        deduped_state_sequence = []
        prior_state = None

        for state in state_sequence:
            if prior_state != state:
                deduped_state_sequence.append(state)
            prior_state = state
        return deduped_state_sequence


def test_db_state_machine(
    mock_local_resolver_storage,  # noqa: F811
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    pipeline(1, 2).resolve(DBStateMachineTestResolver())


def test_list_conversion(
    mock_local_resolver_storage,  # noqa: F811
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    @func
    def alist(a: float, b: float) -> List[float]:
        return [add(a, b), add(a, b)]

    assert alist(1, 2).resolve() == [3, 3]


def test_exceptions(
    mock_local_resolver_storage,  # noqa: F811
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    resolver = CallbackTrackingResolver()

    @func
    def fail():
        raise Exception("FAIL!")

    @func
    def pipeline():
        return fail()

    future = pipeline()

    with pytest.raises(ResolutionError, match="FAIL!") as exc_info:
        future.resolve(resolver)

    assert isinstance(exc_info.value.__context__, CalculatorError)
    assert isinstance(exc_info.value.__context__.__context__, Exception)

    runs, _, _ = get_root_graph(future.id)

    runs_by_id = {run.id: run for run in runs}

    assert runs_by_id[future.id].future_state == FutureState.NESTED_FAILED.value
    assert runs_by_id[future.id].exception_metadata == ExceptionMetadata(
        repr="Failed because the child run failed",
        name="Exception",
        module="builtins",
        ancestors=[],
    )

    assert runs_by_id[future.nested_future.id].future_state == FutureState.FAILED.value
    assert "FAIL!" in runs_by_id[future.nested_future.id].exception_metadata.repr

    parent_callbacks = resolver.callback_by_future_id(future.id)
    nested_callbacks = resolver.callback_by_future_id(future.nested_future.id)
    assert parent_callbacks == [
        "_future_did_schedule",
        "_future_did_run",
        "_future_did_fail",
        "_future_did_terminate",
    ]
    assert nested_callbacks == [
        "_future_did_schedule",
        "_future_did_fail",
        "_future_did_terminate",
    ]


_tried = 0


class SomeException(Exception):
    pass


@func(retry=RetrySettings(exceptions=(SomeException,), retries=3))
def try_three_times():
    global _tried
    _tried += 1
    raise SomeException()


def test_retry(
    mock_local_resolver_storage,  # noqa: F811
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    future = try_three_times()
    resolver = CallbackTrackingResolver()

    with pytest.raises(ResolutionError) as exc_info:
        future.resolve(resolver)

    assert isinstance(exc_info.value.__context__, CalculatorError)
    assert isinstance(exc_info.value.__context__.__context__, SomeException)

    assert future.props.retry_settings.retry_count == 3
    assert future.state == FutureState.FAILED
    assert _tried == 4
    callbacks = resolver.callback_by_future_id(future.id)
    assert callbacks == [
        "_future_did_schedule",
        "_future_did_get_marked_for_retry",
        "_future_did_schedule",
        "_future_did_get_marked_for_retry",
        "_future_did_schedule",
        "_future_did_get_marked_for_retry",
        "_future_did_schedule",
        "_future_did_fail",
        "_future_did_terminate",
    ]


def test_make_resolution():
    @func
    def foo():
        pass

    future = foo()

    resolution = LocalResolver()._make_resolution(future)

    assert resolution.root_id == future.id
    assert resolution.status == ResolutionStatus.SCHEDULED.value
    assert resolution.kind == ResolutionKind.LOCAL.value
    assert resolution.container_image_uris is None
    assert resolution.container_image_uri is None


class RerunTestResolver(LocalResolver):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scheduled_run_counts = defaultdict(lambda: 0)

    def _future_will_schedule(self, future):
        super()._future_will_schedule(future)
        self.scheduled_run_counts[future.calculator.__name__] += 1


def test_rerun_from_here(
    mock_local_resolver_storage,  # noqa: F811
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    future = pipeline(1, 2)

    output = future.resolve()

    runs, _, __ = get_root_graph(future.id)

    for run_id, expected_scheduled_run_counts in {
        future.nested_future.id: dict(add=1),
        future.nested_future.kwargs["a"].id: dict(add=4, add3=1),
        future.nested_future.kwargs["b"].id: dict(add=3, add3=1),
        future.nested_future.kwargs["b"].nested_future.id: dict(add=2),
        future.nested_future.kwargs["b"].nested_future.kwargs["a"].id: dict(add=3),
    }.items():
        new_future = pipeline(1, 2)

        resolver = RerunTestResolver(rerun_from=run_id)

        new_output = new_future.resolve(resolver)

        assert output == new_output

        assert resolver.scheduled_run_counts == expected_scheduled_run_counts


def test_cancel_non_terminal_futures(
    mock_local_resolver_storage,  # noqa: F811
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    resolver = CallbackTrackingResolver()

    @func
    def pass_through(x: int, cancel: bool) -> int:
        if cancel:
            resolver._cancel_non_terminal_futures()
        return x

    @func
    def pipeline() -> int:
        x = pass_through(42, cancel=False)
        x = pass_through(x, cancel=True)
        x = pass_through(x, cancel=False)
        return x

    future = pipeline()
    future.resolve(resolver)
    root_future_id = future.id
    last_func_id = future.nested_future.id
    middle_func_id = future.nested_future.kwargs["x"].id
    first_func_id = future.nested_future.kwargs["x"].kwargs["x"].id

    root_future_callbacks = resolver.callback_by_future_id(root_future_id)
    first_func_callbacks = resolver.callback_by_future_id(first_func_id)
    middle_func_callbacks = resolver.callback_by_future_id(middle_func_id)
    last_func_callbacks = resolver.callback_by_future_id(last_func_id)

    assert root_future_callbacks == [
        "_future_did_schedule",
        "_future_did_run",
        "_future_did_terminate",
    ]
    assert first_func_callbacks == [
        "_future_did_schedule",
        "_future_did_resolve",
        "_future_did_terminate",
    ]
    assert middle_func_callbacks == [
        "_future_did_schedule",
        "_future_did_terminate",
        # final resolved here is just because of the weird way in which
        # we cancel from within a func body. We should technically
        # disallow this kind of transition, see:
        # https://github.com/sematic-ai/sematic/issues/107
        "_future_did_resolve",
        "_future_did_terminate",
    ]
    assert last_func_callbacks == ["_future_did_terminate"]

    root_future_states = resolver.state_sequence_by_future_id(root_future_id)
    first_func_states = resolver.state_sequence_by_future_id(first_func_id)
    middle_func_states = resolver.state_sequence_by_future_id(middle_func_id)
    last_func_states = resolver.state_sequence_by_future_id(last_func_id)

    assert root_future_states == [
        FutureState.SCHEDULED,
        FutureState.RAN,
        FutureState.CANCELED,
    ]
    assert first_func_states == [
        FutureState.SCHEDULED,
        FutureState.RESOLVED,
    ]
    assert middle_func_states == [
        FutureState.SCHEDULED,
        FutureState.CANCELED,
        # see comment in callback assetions above about why this is here
        FutureState.RESOLVED,
    ]
    assert last_func_states == [
        FutureState.CANCELED,
    ]
