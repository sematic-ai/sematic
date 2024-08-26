# Standard Library
import os
import time
from collections import defaultdict
from typing import Any, List, Tuple, Type

# Third-party
import pytest

# Sematic
from sematic import api_client
from sematic.abstract_function import FunctionError
from sematic.abstract_future import AbstractFuture, FutureState
from sematic.api.tests.fixtures import (  # noqa: F401
    mock_auth,
    mock_requests,
    mock_socketio,
    test_client,
)
from sematic.config.tests.fixtures import no_settings_file  # noqa: F401
from sematic.db.db import DB
from sematic.db.models.artifact import Artifact
from sematic.db.models.edge import Edge
from sematic.db.models.factories import make_artifact
from sematic.db.models.resolution import PipelineRunKind, PipelineRunStatus
from sematic.db.models.run import Run
from sematic.db.queries import get_resolution, get_root_graph, get_run
from sematic.db.tests.fixtures import pg_mock, test_db  # noqa: F401
from sematic.function import func
from sematic.retry_settings import RetrySettings
from sematic.runners.local_runner import LocalRunner
from sematic.tests.fixtures import (  # noqa: F401
    DIVERSE_VALUES_WITH_TYPES,
    test_storage,
    valid_client_version,
)
from sematic.utils.exceptions import (
    CancellationError,
    ExceptionMetadata,
    PipelineRunError,
)


@func
def add(a: float, b: float) -> float:
    return a + b


@func
def bad_add(a: float, b: float) -> float:
    raise RuntimeError("Inentional fail")


@func
def add3(a: float, b: float, c: float) -> float:
    return add(add(a, b), c)


@func
def pipeline(a: float, b: float) -> float:
    c = add(a, b)
    d = add3(a, b, c)
    return add(c, d)


@func
def do_cancel(x: float) -> float:
    raise CancellationError("Fake cancellation")


@func
def cancelling_pipeline(a: float, b: float) -> float:
    c = add(a, b)
    d = do_cancel(add3(a, b, c))
    return bad_add(c, d)


def test_single_function(
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    future = add(1, 2)

    result = LocalRunner().run(future.set(name="AAA"))

    assert result == 3

    runs, artifacts, edges = get_root_graph(future.id)

    assert len(runs) == 1
    assert len(artifacts) == 3
    assert len(edges) == 3

    artifact_a, _ = make_artifact(1.0, float)
    artifact_b, _ = make_artifact(2.0, float)
    artifact_output, _ = make_artifact(3.0, float)

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

    assert result == api_client.get_run_output(future.id)


@func
def add_add_add(a: float, b: float) -> float:
    aa = add(a, b)
    bb = add(a, aa)
    return add(bb, aa)


def test_add_add(
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    future = add_add_add(1, 2)

    result = LocalRunner().run(future)

    assert result == 7

    runs, artifacts, edges = get_root_graph(future.id)

    assert len(runs) == 4
    assert len(artifacts) == 5
    assert len(edges) == 10


def test_pipeline(
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    runner = CallbackTrackingRunner()
    future = pipeline(3, 5)

    result = runner.run(future)

    assert result == 24
    assert isinstance(result, float)
    assert future.state == FutureState.RESOLVED

    runs, artifacts, edges = get_root_graph(future.id)
    assert get_resolution(future.id).status == PipelineRunStatus.COMPLETE.value

    assert len(runs) == 6
    assert len(artifacts) == 5
    assert len(edges) == 16
    pipeline_callbacks = runner.callback_by_future_id(future.id)
    final_add_callbacks = runner.callback_by_future_id(future.nested_future.id)
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


def test_cancelling_pipeline(
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    # note that this doesn't test the full cancellation flow,
    # which would require using an OS signal on this process.
    # It should at least confirm that we invoke some of the
    # cleanup logic though.
    runner = CallbackTrackingRunner()
    future = cancelling_pipeline(3, 5)

    with pytest.raises(CancellationError):
        runner.run(future)

    root_run = get_run(future.id)
    assert root_run.future_state == FutureState.CANCELED.value

    runs, _, __ = get_root_graph(future.id)

    for run in runs:
        assert run.future_state in (
            FutureState.CANCELED.value,
            FutureState.RESOLVED.value,
        )

    pipeline_run = get_resolution(root_run.id)
    assert pipeline_run.status == PipelineRunStatus.CANCELED.value


def test_failure(
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

    runner = LocalRunner()
    future = pipeline()

    with pytest.raises(PipelineRunError, match="some message") as exc_info:
        runner.run(future)

    assert isinstance(exc_info.value.__context__, FunctionError)
    assert isinstance(exc_info.value.__context__.__context__, CustomException)

    assert get_resolution(future.id).status == PipelineRunStatus.FAILED.value
    expected_states = dict(
        pipeline=FutureState.NESTED_FAILED,
        success=FutureState.RESOLVED,
        failure=FutureState.FAILED,
    )

    for future in runner._futures:
        assert future.state == expected_states[future.function.__name__]


def test_pre_pipeline_run_creation_failure(
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    class CustomException(Exception):
        pass

    def do_fail(*args, **kwargs):
        raise CustomException("Custom exception")

    @func
    def pipeline() -> None:
        return None

    runner = LocalRunner()
    runner._make_pipeline_run = do_fail
    future = pipeline()

    with pytest.raises(CustomException):
        # this confirms the exception isn't swallowed by another when trying
        # to fail the pipeline run.
        runner.run(future)


def test_runner_error(
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

    runner = LocalRunner()

    def intentional_fail(*_, **__):
        raise ValueError("some message")

    # Random failure in pipeline run logic
    runner._future_did_resolve = intentional_fail
    future = pipeline()

    with pytest.raises(PipelineRunError, match="some message") as exc_info:
        runner.run(future)

    # this test doesn't really go through the entire Runner logic due to
    # the custom setting of _future_did_resolve above, so no FunctionError here
    # TODO: replace with testing logic that goes through the entire tested code logic
    assert isinstance(exc_info.value.__context__, ValueError)

    assert get_resolution(future.id).status == PipelineRunStatus.FAILED.value
    assert get_run(future.id).future_state == FutureState.NESTED_FAILED.value
    assert get_run(future.nested_future.id).future_state == FutureState.CANCELED.value
    assert (
        get_run(future.nested_future.kwargs["x"].id).future_state
        == FutureState.FAILED.value
    )
    assert (
        get_run(future.nested_future.kwargs["y"].id).future_state
        == FutureState.CANCELED.value
    )


class DBStateMachineTestRunner(LocalRunner):
    def _future_will_schedule(self, future) -> None:
        super()._future_will_schedule(future)

        run = self._get_run(future.id)

        assert run.id == future.id
        assert run.future_state == FutureState.SCHEDULED.value
        assert run.name == future.function.__name__
        assert run.function_path == "{}.{}".format(
            future.function.__module__, future.function.__name__
        )
        assert run.parent_id == (
            future.parent_future.id if not future.is_root_future() else None
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


class CallbackTrackingRunner(LocalRunner):
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
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    DBStateMachineTestRunner().run(pipeline(1, 2))


def test_list_conversion(
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    @func
    def alist(a: float, b: float) -> List[float]:
        return [add(a, b), add(a, b)]

    assert LocalRunner().run(alist(1, 2)) == [3, 3]


def test_exceptions(
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    runner = CallbackTrackingRunner()

    @func
    def fail():
        raise Exception("FAIL!")

    @func
    def pipeline():
        return fail()

    future = pipeline()

    with pytest.raises(PipelineRunError, match="FAIL!") as exc_info:
        runner.run(future)

    assert isinstance(exc_info.value.__context__, FunctionError)
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

    parent_callbacks = runner.callback_by_future_id(future.id)
    nested_callbacks = runner.callback_by_future_id(future.nested_future.id)
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
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    future = try_three_times()
    runner = CallbackTrackingRunner()

    with pytest.raises(PipelineRunError) as exc_info:
        runner.run(future)

    assert isinstance(exc_info.value.__context__, FunctionError)
    assert isinstance(exc_info.value.__context__.__context__, SomeException)

    assert future.props.retry_settings.retry_count == 3
    assert future.state == FutureState.FAILED
    assert _tried == 4
    callbacks = runner.callback_by_future_id(future.id)
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


def test_make_pipeline_run():
    @func
    def foo():
        pass

    future = foo()

    pipeline_run = LocalRunner()._make_pipeline_run(future)

    assert pipeline_run.root_id == future.id
    assert pipeline_run.status == PipelineRunStatus.SCHEDULED.value
    assert pipeline_run.kind == PipelineRunKind.LOCAL.value
    assert pipeline_run.container_image_uris is None
    assert pipeline_run.container_image_uri is None


class RerunTestRunner(LocalRunner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scheduled_run_counts = defaultdict(lambda: 0)

    def _future_will_schedule(self, future):
        super()._future_will_schedule(future)
        self.scheduled_run_counts[future.function.__name__] += 1


def test_rerun_from_here(
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
    test_storage,  # noqa: F811
):
    future = pipeline(1, 2)

    output = LocalRunner().run(future)

    runs, _, __ = get_root_graph(future.id)

    for run_id, expected_scheduled_run_counts in {
        future.nested_future.id: dict(add=1),
        future.nested_future.kwargs["a"].id: dict(add=4, add3=1),
        future.nested_future.kwargs["b"].id: dict(add=3, add3=1),
        future.nested_future.kwargs["b"].nested_future.id: dict(add=2),
        future.nested_future.kwargs["b"].nested_future.kwargs["a"].id: dict(add=3),
    }.items():
        new_future = pipeline(1, 2)

        runner = RerunTestRunner(rerun_from=run_id)

        new_output = runner.run(new_future)

        assert output == new_output

        assert runner.scheduled_run_counts == expected_scheduled_run_counts


def test_cancel_non_terminal_futures(
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    runner = CallbackTrackingRunner()

    @func
    def pass_through(x: int, cancel: bool) -> int:
        if cancel:
            runner._cancel_non_terminal_futures()
        return x

    @func
    def pipeline() -> int:
        x = pass_through(42, cancel=False)
        x = pass_through(x, cancel=True)
        x = pass_through(x, cancel=False)
        return x

    future = pipeline()
    runner.run(future)
    root_future_id = future.id
    last_func_id = future.nested_future.id
    middle_func_id = future.nested_future.kwargs["x"].id
    first_func_id = future.nested_future.kwargs["x"].kwargs["x"].id

    root_future_callbacks = runner.callback_by_future_id(root_future_id)
    first_func_callbacks = runner.callback_by_future_id(first_func_id)
    middle_func_callbacks = runner.callback_by_future_id(middle_func_id)
    last_func_callbacks = runner.callback_by_future_id(last_func_id)

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

    root_future_states = runner.state_sequence_by_future_id(root_future_id)
    first_func_states = runner.state_sequence_by_future_id(first_func_id)
    middle_func_states = runner.state_sequence_by_future_id(middle_func_id)
    last_func_states = runner.state_sequence_by_future_id(last_func_id)

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
        # see comment in callback assertions above about why this is here
        FutureState.RESOLVED,
    ]
    assert last_func_states == [
        FutureState.CANCELED,
    ]


def _get_runs_and_artifacts(db: DB) -> List[Tuple[Run, Artifact]]:
    with db.get_session() as session:
        return (
            session.query(Run, Artifact)  # type: ignore
            .join(Edge, Edge.source_run_id == Run.id)
            .filter(Edge.artifact_id == Artifact.id)
            .order_by(Run.created_at)
            .all()
        )


@pytest.mark.parametrize("value_and_type", DIVERSE_VALUES_WITH_TYPES)
def test_cached_output_happy(
    value_and_type: Tuple[Any, Type],
    mock_socketio,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
):
    value, T = value_and_type

    @func(cache=True)
    def cache_func(param: T) -> T:  # type: ignore
        return param

    # original run:
    runner = LocalRunner(cache_namespace="test_namespace")
    original_future = cache_func(param=value)
    output = runner.run(original_future)

    assert output == value

    # second run, which should be cached:
    # runners are single-use, so we instantiate a new one
    runner = LocalRunner(cache_namespace="test_namespace")
    cache_future = cache_func(param=value)
    output = runner.run(cache_future)

    assert output == value

    # get the saved runs and artifacts from the test db
    db_values = _get_runs_and_artifacts(test_db)

    assert len(db_values) == 2
    original_run, original_artifact = db_values[0]
    cache_run, cache_artifact = db_values[1]

    assert original_run.cache_key == cache_run.cache_key
    assert original_run.id == original_future.id
    assert cache_run.id == cache_future.id
    assert original_artifact == cache_artifact


def test_cached_output_different_namespaces(
    mock_socketio,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
):
    @func(cache=True)
    def cache_func(param: int) -> int:  # type: ignore
        return param

    # original run:
    runner = LocalRunner(cache_namespace="test_namespace1")
    future1 = cache_func(param=42)
    output1 = runner.run(future1)

    assert output1 == 42

    # second run, which should be cached:
    # runners are single-use, so we instantiate a new one
    runner = LocalRunner(cache_namespace="test_namespace2")
    future2 = cache_func(param=42)
    output2 = runner.run(future2)

    assert output2 == 42

    # get the saved runs and artifacts from the test db
    db_values = _get_runs_and_artifacts(test_db)

    assert len(db_values) == 2
    run1, artifact1 = db_values[0]
    run2, artifact2 = db_values[1]

    assert run1.cache_key != run2.cache_key
    assert run1.id == future1.id
    assert run2.id == future2.id
    # we currently address artifacts by content
    # if this ever changes, this must be updated to `!=`,
    # and this added: with pytest.raises(ValueError): artifact1.assert_matches(artifact2)
    assert artifact1 == artifact2


def test_cached_output_different_funcs(
    mock_socketio,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
):
    @func(cache=True)
    def cache_func1(param: int) -> int:  # type: ignore
        return param

    @func(cache=True)
    def cache_func2(param: int) -> int:  # type: ignore
        return param

    # original run:
    runner = LocalRunner(cache_namespace="test_namespace")
    future1 = cache_func1(param=42)
    output1 = runner.run(future1)

    assert output1 == 42

    # second run, which should be cached:
    # runners are single-use, so we instantiate a new one
    runner = LocalRunner(cache_namespace="test_namespace")
    future2 = cache_func2(param=42)
    output2 = runner.run(future2)

    assert output2 == 42

    # get the saved runs and artifacts from the test db
    db_values = _get_runs_and_artifacts(test_db)

    assert len(db_values) == 2
    run1, artifact1 = db_values[0]
    run2, artifact2 = db_values[1]

    assert run1.cache_key != run2.cache_key
    assert run1.id == future1.id
    assert run2.id == future2.id
    # we currently address artifacts by content
    # if this ever changes, this must be updated to `!=`,
    # and this added: with pytest.raises(ValueError): artifact1.assert_matches(artifact2)
    assert artifact1 == artifact2


def test_cached_output_different_inputs(
    mock_socketio,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
):
    @func(cache=True)
    def cache_func(param: int) -> int:  # type: ignore
        return param

    # original run:
    runner = LocalRunner(cache_namespace="test_namespace")
    future1 = cache_func(param=42)
    output1 = runner.run(future1)

    assert output1 == 42

    # second run, which should be cached:
    # runners are single-use, so we instantiate a new one
    runner = LocalRunner(cache_namespace="test_namespace")
    future2 = cache_func(param=43)
    output2 = runner.run(future2)

    assert output2 == 43

    # get the saved runs and artifacts from the test db
    db_values = _get_runs_and_artifacts(test_db)

    assert len(db_values) == 2
    run1, artifact1 = db_values[0]
    run2, artifact2 = db_values[1]

    assert run1.cache_key != run2.cache_key
    assert run1.id == future1.id
    assert run2.id == future2.id
    assert artifact1 != artifact2

    with pytest.raises(ValueError):
        artifact1.assert_matches(artifact2)


def test_subprocess_signal_handling(
    no_settings_file,  # noqa: F811
    mock_socketio,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
):
    @func
    def fork_func(param: int) -> int:  # type: ignore
        subprocess_pid = os.fork()

        if subprocess_pid == 0:
            time.sleep(1)
            # sys.exit(1) would mess up pytest
            os._exit(1)

        os.kill(subprocess_pid, 15)
        os.waitpid(subprocess_pid, 0)
        return param

    future = fork_func(param=42)
    result = LocalRunner().run(future)

    # assert killing the subprocess did not cancel the pipeline run
    assert result == 42


def test_subprocess_no_cleanup(
    no_settings_file,  # noqa: F811
    mock_socketio,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
):
    @func
    def fork_func(param: int) -> int:  # type: ignore
        subprocess_pid = os.fork()

        if subprocess_pid == 0:
            return param

        os.waitpid(subprocess_pid, 0)
        time.sleep(1)
        return param

    future = fork_func(param=42)
    result = LocalRunner().run(future)

    # assert the subprocess did not execute worker code,
    # messing up the actual worker's workflow
    assert result == 42


def test_subprocess_error(
    no_settings_file,  # noqa: F811
    mock_socketio,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
):
    @func
    def fork_func(param: int) -> int:  # type: ignore
        subprocess_pid = os.fork()

        if subprocess_pid == 0:
            # sys.exit(1) would mess up pytest
            os._exit(1)

        os.waitpid(subprocess_pid, 0)
        time.sleep(1)
        return param

    future = fork_func(param=42)
    result = LocalRunner().run(future)

    # assert the subprocess' death did not cancel the pipeline run
    assert result == 42
