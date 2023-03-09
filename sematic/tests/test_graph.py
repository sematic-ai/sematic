# Third-party
import pytest

# Sematic
import sematic.api_client as api_client
from sematic.abstract_future import FutureState
from sematic.api.tests.fixtures import (  # noqa: F401
    mock_auth,
    mock_broadcasts,
    mock_requests,
    mock_socketio,
    test_client,
)
from sematic.calculator import func
from sematic.db.tests.fixtures import test_db  # noqa: F401
from sematic.graph import Graph
from sematic.resolvers.local_resolver import LocalResolver


@func
def add(a: float, b: float) -> float:
    return a + b


@func
def add3(a: float, b: float, c: float) -> float:
    return add(add(a, b), c)


@func
def pipeline(a: float, b: float, c: float) -> float:
    d = add3(add(a, b), add(b, c), add(a, c))
    return add3(d, b, c)


def test_clone_futures(
    mock_auth,  # noqa: F811
    mock_socketio,  # noqa: F811
    mock_broadcasts,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
):
    future = pipeline(1, 2, 3)
    resolver = LocalResolver()
    output = future.resolve(resolver)

    assert output == 17

    runs, artifacts, edges = api_client.get_graph(future.id, root=True)

    runs_by_id = {run.id: run for run in runs}

    graph = Graph(runs=runs, edges=edges, artifacts=artifacts)

    cloned_graph = graph.clone_futures()

    assert len(cloned_graph.futures_by_original_id) == len(runs)

    root_future = cloned_graph.futures_by_original_id[future.id]

    assert root_future.state == FutureState.RESOLVED
    assert root_future.calculator._func is pipeline._func
    assert root_future.is_root_future()
    # the entire pipeline resolution was cloned,
    # so the root run was never actually executed
    assert root_future.original_future_id == future.id

    for original_run_id, future_ in cloned_graph.futures_by_original_id.items():
        original_run = runs_by_id[original_run_id]
        # No reset so state should be the same
        assert future.state.value == original_run.future_state
        assert future.original_future_id == original_run.original_run_id

        # Parent future should exist and be the correct one
        if original_run.parent_id is not None:
            parent_run = runs_by_id[original_run.parent_id]
            assert (
                cloned_graph.futures_by_original_id[parent_run.id]
                is future_.parent_future
            )

        # Making sure all future kwargs are correct
        for input_edge in graph._edges_by_destination_id[original_run.id]:
            artifact = graph._artifacts_by_id[input_edge.artifact_id]
            assert (
                cloned_graph.input_artifacts[future_.id][input_edge.destination_name]
                is artifact
            )

            if input_edge.source_run_id is None:
                value = api_client.get_artifact_value(artifact)
                assert future_.kwargs[input_edge.destination_name] == value
            else:
                upstream_future = cloned_graph.futures_by_original_id[
                    input_edge.source_run_id
                ]
                assert future_.kwargs[input_edge.destination_name] is upstream_future

        # Making sure output values are correct
        for output_edge in graph._edges_by_source_id[original_run_id]:
            artifact = graph._artifacts_by_id[output_edge.artifact_id]
            assert cloned_graph.output_artifacts[future_.id] is artifact

            value = api_client.get_artifact_value(artifact)
            assert future_.value == value
            if output_edge.destination_run_id is not None:
                downstream_run = runs_by_id[output_edge.destination_run_id]
                downstream_future = cloned_graph.futures_by_original_id[
                    downstream_run.id
                ]
                assert downstream_future.kwargs[output_edge.destination_name] is future_


def test_clone_futures_reset(
    mock_auth,  # noqa: F811
    mock_socketio,  # noqa: F811
    mock_broadcasts,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
):
    future = pipeline(1, 2, 3)
    resolver = LocalResolver()
    future.resolve(resolver)

    runs, artifacts, edges = api_client.get_graph(future.id, root=True)

    graph = Graph(runs=runs, edges=edges, artifacts=artifacts)

    reset_from_run_id = future.nested_future.kwargs["a"].nested_future.kwargs["a"].id

    cloned_graph = graph.clone_futures(reset_from=reset_from_run_id)

    root_future = cloned_graph.futures_by_original_id[future.id]

    assert root_future.state == FutureState.RAN
    assert root_future.calculator._func is pipeline._func
    assert root_future.is_root_future()
    assert root_future.original_future_id is None

    second_add3_future = root_future.nested_future
    assert second_add3_future.state == FutureState.CREATED
    assert second_add3_future.original_future_id is None

    # Check that the second add3 future has no children
    assert not any(
        future_.parent_future is second_add3_future
        for future_ in cloned_graph.futures_by_original_id.values()
    )

    first_add3_future = second_add3_future.kwargs["a"]
    assert first_add3_future.state is FutureState.RAN
    assert first_add3_future.original_future_id is None

    first_add3_child_futures = [
        future_
        for future_ in cloned_graph.futures_by_original_id.values()
        if future_.parent_future is first_add3_future
    ]

    assert len(first_add3_child_futures) == 2
    assert all(
        future_.state is FutureState.CREATED for future_ in first_add3_child_futures
    )
    assert all(
        future_.original_future_id is None for future_ in first_add3_child_futures
    )

    top_level_add_futures = [
        future_
        for future_ in cloned_graph.futures_by_original_id.values()
        if future_.parent_future is root_future
        and future_ not in {first_add3_future, second_add3_future}
    ]

    assert len(top_level_add_futures) == 3
    assert all(
        future_.state is FutureState.RESOLVED for future_ in top_level_add_futures
    )

    top_level_add_futures_ids = {
        id
        for id, future_ in cloned_graph.futures_by_original_id.items()
        if future_.calculator._func is add._func
    }
    top_level_add_futures_original_ids = {
        future_.original_future_id for future_ in top_level_add_futures
    }

    assert len(top_level_add_futures_original_ids) == 3
    assert top_level_add_futures_original_ids.issubset(top_level_add_futures_ids)


@func
def add_fail(a: float, b: float) -> float:
    raise Exception("fail")


@func
def add4(a: float, b: float, c: float, d: float) -> float:
    return add(add(a, b), add_fail(c, d))


def test_reset_failed(
    mock_auth,  # noqa: F811
    mock_socketio,  # noqa: F811
    mock_broadcasts,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
):
    resolver = LocalResolver()

    future = add4(1, 2, 3, 4)

    with pytest.raises(Exception):
        future.resolve(resolver)

    runs, artifacts, edges = api_client.get_graph(future.id, root=True)

    graph = Graph(runs=runs, edges=edges, artifacts=artifacts)

    reset_from_run_id = future.nested_future.kwargs["a"].id

    cloned_graph = graph.clone_futures(reset_from=reset_from_run_id)

    root_future = cloned_graph.futures_by_original_id[future.id]

    assert root_future.state is FutureState.RAN
    assert root_future.nested_future.state is FutureState.CREATED
    assert root_future.nested_future.kwargs["a"].state is FutureState.CREATED
    assert root_future.nested_future.kwargs["b"].state is FutureState.CREATED


@func
def order_test() -> float:
    return add3(add3(1, 2, 3), 2, 3)


def test_run_execution_ordering(
    mock_auth,  # noqa: F811
    mock_socketio,  # noqa: F811
    mock_broadcasts,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
):
    future = order_test()
    future.resolve(LocalResolver())

    runs, artifacts, edges = api_client.get_graph(future.id, root=True)

    graph = Graph(runs=runs, edges=edges, artifacts=artifacts)

    run_ids_by_execution_order = graph._sorted_run_ids_by_layer(
        run_sorter=graph._execution_order
    )

    expected_order = [
        # Layer 0
        future.id,
        # Layer 1
        future.nested_future.kwargs["a"].id,
        future.nested_future.id,
        # Layer 1.1
        future.nested_future.kwargs["a"].nested_future.kwargs["a"].id,
        future.nested_future.kwargs["a"].nested_future.id,
        # Layer 1.2
        future.nested_future.nested_future.kwargs["a"].id,
        future.nested_future.nested_future.id,
    ]

    assert run_ids_by_execution_order == expected_order


def test_run_reverse_ordering(
    mock_auth,  # noqa: F811
    mock_socketio,  # noqa: F811
    mock_broadcasts,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
):
    future = order_test()
    future.resolve(LocalResolver())

    runs, artifacts, edges = api_client.get_graph(future.id, root=True)

    graph = Graph(runs=runs, edges=edges, artifacts=artifacts)

    run_ids_by_reverse_order = graph._sorted_run_ids_by_layer(
        run_sorter=graph._reverse_execution_order
    )

    expected_order = [
        # Layer 0
        future.id,
        # Layer 1
        future.nested_future.id,
        future.nested_future.kwargs["a"].id,
        # Layer 1.2
        future.nested_future.nested_future.id,
        future.nested_future.nested_future.kwargs["a"].id,
        # Layer 1.1
        future.nested_future.kwargs["a"].nested_future.id,
        future.nested_future.kwargs["a"].nested_future.kwargs["a"].id,
    ]

    assert run_ids_by_reverse_order == expected_order


@func
def pipeline_fail(a: int) -> int:
    b = add_fail(a, a)
    c = add(a, b)
    return add(a, c)


def test_nested_fail(
    mock_auth,  # noqa: F811
    mock_socketio,  # noqa: F811
    mock_broadcasts,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
):
    future = pipeline_fail(1)
    resolver = LocalResolver()

    with pytest.raises(Exception, match="fail"):
        future.resolve(resolver)

    runs, artifacts, edges = api_client.get_graph(future.id, root=True)

    graph = Graph(runs=runs, edges=edges, artifacts=artifacts)
    for run in runs:
        graph.clone_futures(reset_from=run.id)
