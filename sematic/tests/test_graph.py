# Third-party
import pytest

# Sematic
import sematic.api_client as api_client
from sematic.abstract_future import FutureState
from sematic.api.tests.fixtures import (
    mock_auth,  # noqa: F401
    mock_requests,  # noqa: F401
    mock_socketio,  # noqa: F401
    test_client,  # noqa: F401; noqa: F401
)
from sematic.db.tests.fixtures import test_db  # noqa: F401
from sematic.function import func
from sematic.graph import Graph
from sematic.runners.local_runner import LocalRunner


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
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
):
    future = pipeline(1, 2, 3)
    runner = LocalRunner()
    output = runner.run(future)

    assert output == 17

    runs, artifacts, edges = api_client.get_graph(future.id, root=True)

    runs_by_id = {run.id: run for run in runs}

    graph = Graph(runs=runs, edges=edges, artifacts=artifacts)

    cloned_graph = graph.clone_futures()

    assert len(cloned_graph.futures_by_run_id) == len(runs)

    root_future = cloned_graph.futures_by_run_id[future.id]

    assert root_future.state == FutureState.RESOLVED
    assert root_future.function._func is pipeline._func
    assert root_future.is_root_future()
    # the entire pipeline run was cloned,
    # so the root run was never actually executed
    assert root_future.original_future_id == future.id

    for original_run_id, future_ in cloned_graph.futures_by_run_id.items():
        original_run = runs_by_id[original_run_id]
        # No reset so state should be the same
        assert future.state.value == original_run.future_state
        assert future.original_future_id == original_run.original_run_id

        # Parent future should exist and be the correct one
        if original_run.parent_id is not None:
            parent_run = runs_by_id[original_run.parent_id]
            assert cloned_graph.futures_by_run_id[parent_run.id] is future_.parent_future

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
                upstream_future = cloned_graph.futures_by_run_id[input_edge.source_run_id]
                assert future_.kwargs[input_edge.destination_name] is upstream_future

        # Making sure output values are correct
        for output_edge in graph._edges_by_source_id[original_run_id]:
            artifact = graph._artifacts_by_id[output_edge.artifact_id]
            assert cloned_graph.output_artifacts[future_.id] is artifact

            value = api_client.get_artifact_value(artifact)
            assert future_.value == value
            if output_edge.destination_run_id is not None:
                downstream_run = runs_by_id[output_edge.destination_run_id]
                downstream_future = cloned_graph.futures_by_run_id[downstream_run.id]
                assert downstream_future.kwargs[output_edge.destination_name] is future_


def test_to_future_graph(
    mock_auth,  # noqa: F811
    mock_socketio,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
):
    name = "the name"
    original_future = pipeline(1, 2, 3).set(name=name)
    runner = LocalRunner()
    result = runner.run(original_future)

    runs, artifacts, edges = api_client.get_graph(original_future.id, root=True)

    graph = Graph(runs=runs, edges=edges, artifacts=artifacts)
    future_graph = graph.to_future_graph()
    root_future = future_graph.futures_by_run_id[original_future.id]
    assert root_future.props.name == name
    assert root_future.kwargs == {"a": 1.0, "b": 2.0, "c": 3.0}
    assert root_future.function is pipeline

    nested_future = root_future.nested_future
    assert nested_future.function is add3
    d_future = nested_future.kwargs["a"]
    assert nested_future.kwargs["b"] == 2.0
    assert nested_future.kwargs["c"] == 3.0

    assert d_future.function is add3

    add_future1 = d_future.kwargs["a"]
    add_future2 = d_future.kwargs["b"]
    add_future3 = d_future.kwargs["c"]

    assert add_future1.function is add
    assert add_future2.function is add
    assert add_future3.function is add

    assert add_future1.kwargs == {"a": 1.0, "b": 2.0}
    assert add_future2.kwargs == {"a": 2.0, "b": 3.0}
    assert add_future3.kwargs == {"a": 1.0, "b": 3.0}

    assert future_graph.output_artifacts[add_future1.id].json_summary == "3.0"
    assert future_graph.output_artifacts[add_future2.id].json_summary == "5.0"
    assert future_graph.output_artifacts[add_future3.id].json_summary == "4.0"
    assert future_graph.output_artifacts[root_future.id].json_summary == str(result)

    assert future_graph.input_artifacts[add_future1.id]["a"].json_summary == "1.0"
    assert future_graph.input_artifacts[add_future1.id]["b"].json_summary == "2.0"


def test_clone_futures_reset(
    mock_auth,  # noqa: F811
    mock_socketio,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
):
    future = pipeline(1, 2, 3)
    runner = LocalRunner()
    runner.run(future)

    runs, artifacts, edges = api_client.get_graph(future.id, root=True)

    graph = Graph(runs=runs, edges=edges, artifacts=artifacts)

    reset_from_run_id = future.nested_future.kwargs["a"].nested_future.kwargs["a"].id

    cloned_graph = graph.clone_futures(reset_from=reset_from_run_id)

    root_future = cloned_graph.futures_by_run_id[future.id]

    assert root_future.state == FutureState.RAN
    assert root_future.function._func is pipeline._func
    assert root_future.is_root_future()
    assert root_future.original_future_id is None

    second_add3_future = root_future.nested_future
    assert second_add3_future.state == FutureState.CREATED
    assert second_add3_future.original_future_id is None

    # Check that the second add3 future has no children
    assert not any(
        future_.parent_future is second_add3_future
        for future_ in cloned_graph.futures_by_run_id.values()
    )

    first_add3_future = second_add3_future.kwargs["a"]
    assert first_add3_future.state is FutureState.RAN
    assert first_add3_future.original_future_id is None

    first_add3_child_futures = [
        future_
        for future_ in cloned_graph.futures_by_run_id.values()
        if future_.parent_future is first_add3_future
    ]

    assert len(first_add3_child_futures) == 2
    assert all(
        future_.state is FutureState.CREATED for future_ in first_add3_child_futures
    )
    assert all(future_.original_future_id is None for future_ in first_add3_child_futures)

    top_level_add_futures = [
        future_
        for future_ in cloned_graph.futures_by_run_id.values()
        if future_.parent_future is root_future
        and future_ not in {first_add3_future, second_add3_future}
    ]

    assert len(top_level_add_futures) == 3
    assert all(future_.state is FutureState.RESOLVED for future_ in top_level_add_futures)

    top_level_add_futures_ids = {
        id
        for id, future_ in cloned_graph.futures_by_run_id.items()
        if future_.function._func is add._func
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
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
):
    runner = LocalRunner()

    future = add4(1, 2, 3, 4)

    with pytest.raises(Exception):
        runner.run(future)

    runs, artifacts, edges = api_client.get_graph(future.id, root=True)

    graph = Graph(runs=runs, edges=edges, artifacts=artifacts)

    reset_from_run_id = future.nested_future.kwargs["a"].id

    cloned_graph = graph.clone_futures(reset_from=reset_from_run_id)

    root_future = cloned_graph.futures_by_run_id[future.id]

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
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
):
    future = order_test()
    LocalRunner().run(future)

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
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
):
    future = order_test()
    LocalRunner().run(future)

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
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
):
    future = pipeline_fail(1)
    runner = LocalRunner()

    with pytest.raises(Exception, match="fail"):
        runner.run(future)

    runs, artifacts, edges = api_client.get_graph(future.id, root=True)

    graph = Graph(runs=runs, edges=edges, artifacts=artifacts)
    for run in runs:
        graph.clone_futures(reset_from=run.id)
