# Standard Library
from typing import List, Optional
from unittest import mock

# Third-party
import pytest

# Sematic
import sematic.api_client as api_client
from sematic.abstract_future import FutureState
from sematic.api.tests.fixtures import (  # noqa: F401
    mock_auth,
    mock_requests,
    mock_socketio,
    test_client,
)
from sematic.db.models.edge import Edge
from sematic.db.models.factories import make_artifact
from sematic.db.models.resolution import PipelineRunKind, PipelineRunStatus
from sematic.db.queries import get_root_graph, get_run, save_graph, save_resolution
from sematic.db.tests.fixtures import make_run  # noqa: F401
from sematic.db.tests.fixtures import persisted_resolution  # noqa: F401
from sematic.db.tests.fixtures import persisted_run  # noqa: F401
from sematic.db.tests.fixtures import pg_mock  # noqa: F401
from sematic.db.tests.fixtures import run  # noqa: F401
from sematic.db.tests.fixtures import (  # noqa: F401
    allow_any_run_state_transition,
    test_db,
)
from sematic.function import func
from sematic.graph import RerunMode
from sematic.runners.cloud_runner import CloudRunner
from sematic.tests.fixtures import valid_client_version  # noqa: F401
from sematic.utils.env import environment_variables


@func(base_image_tag="cuda", standalone=True)
def add(a: float, b: float) -> float:
    return a + b


# TODO: support pipeline args
@func
def pipeline() -> float:
    return add(1, 2)


class InstrumentedCloudRunner(CloudRunner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _INSTRUMENTED_INSTANCES.append(self)
        self._init_args = (args, kwargs)
        self._run_called_with = None
        self._detach_pipeline_run_called_with = None

    def run(self, future):  # noqa: F811
        self._run_called_with = future
        super().run(future)

    def _detach_pipeline_run(self, future):
        self._detach_pipeline_run_called_with = future


_INSTRUMENTED_INSTANCES: List[InstrumentedCloudRunner] = []


@mock.patch("sematic.api_client.update_run_future_states")
@mock.patch("sematic.runners.cloud_runner.get_image_uris")
@mock.patch("sematic.api_client.schedule_run")
@mock.patch("sematic.api_client.schedule_pipeline_run")
@mock.patch("kubernetes.config.load_kube_config")
def test_simulate_cloud_exec(
    mock_load_kube_config: mock.MagicMock,
    mock_schedule_pipeline_run: mock.MagicMock,
    mock_schedule_run: mock.MagicMock,
    mock_get_images: mock.MagicMock,
    mock_update_run_future_states: mock.MagicMock,
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    mock_requests,  # noqa: F811
    test_db,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    # On the user's machine
    runner = CloudRunner(detach=True)

    future = pipeline()
    images = {
        "default": "default_image",
        "cuda": "cuda_image",
    }
    mock_get_images.return_value = images

    result = runner.run(future)
    add_run_ids = []

    assert result == future.id

    def fake_schedule(run_id):
        if run_id == future.id:
            raise RuntimeError("Root future should not need scheduling--it's inline!")
        run = api_client.get_run(run_id)  # noqa: F811
        if "add" in run.function_path:
            add_run_ids.append(run_id)
        run.future_state = FutureState.SCHEDULED
        api_client.save_graph(run.id, runs=[run], artifacts=[], edges=[])
        return run

    mock_schedule_run.side_effect = fake_schedule

    def fake_update_run_future_states(run_ids):
        updates = {}
        for run_id in run_ids:
            if run_id == future.id:
                raise RuntimeError("Root future should not need updating--it's inline!")
            run = api_client.get_run(run_id)  # noqa: F811
            run.future_state = FutureState.RESOLVED
            updates[run.id] = FutureState.RESOLVED
            edge = driver_runner._get_output_edges(run.id)[0]
            artifact, payloads = make_artifact(3, int)
            edge.artifact_id = artifact.id
            api_client.save_graph(
                run.id, runs=[run], artifacts=[artifact], edges=[edge]
            )
            api_client.store_payloads(payloads)
            driver_runner._refresh_graph(run.id)
        return updates

    mock_update_run_future_states.side_effect = fake_update_run_future_states

    mock_schedule_pipeline_run.assert_called_once_with(
        pipeline_run_id=future.id,
        max_parallelism=None,
        rerun_from=None,
        rerun_mode=None,
    )
    assert (
        api_client.get_pipeline_run(future.id).status == PipelineRunStatus.CREATED.value
    )

    pipeline_run = api_client.get_pipeline_run(future.id)
    root_run = api_client.get_run(future.id)
    assert root_run.container_image_uri == images["default"]
    pipeline_run.status = PipelineRunStatus.SCHEDULED
    api_client.save_pipeline_run(pipeline_run)
    mock_schedule_run.assert_not_called()

    # In the driver job

    runs, artifacts, edges = api_client.get_graph(future.id)

    driver_runner = CloudRunner(detach=False, _is_running_remotely=True)

    driver_runner.set_graph(runs=runs, artifacts=artifacts, edges=edges)
    assert (
        api_client.get_pipeline_run(future.id).status
        == PipelineRunStatus.SCHEDULED.value
    )
    output = driver_runner.run(future)

    assert output == 3
    assert (
        api_client.get_pipeline_run(future.id).status
        == PipelineRunStatus.COMPLETE.value
    )
    assert mock_get_images.call_count == 1
    assert driver_runner._get_tagged_image("cuda") == images["cuda"]
    assert len(add_run_ids) == 1
    add_run = api_client.get_run(add_run_ids[0])
    assert add_run.container_image_uri == images["cuda"]

    # cheap way of confirming no k8s calls were made
    mock_load_kube_config.assert_not_called()


@pytest.mark.parametrize(
    "max_parallelism, expected_validates",
    (
        (None, True),
        (0, False),
        (-1, False),
        (1, True),
        (10, True),
    ),
)
def test_max_parallelism_validation(max_parallelism, expected_validates):
    try:
        CloudRunner(max_parallelism=max_parallelism)
    except ValueError:
        assert not expected_validates
        return
    assert expected_validates


@mock.patch(
    "sematic.runners.cloud_runner.get_image_uris",
    return_value={"default": "foo", "cuda": "bar"},
)
@pytest.mark.parametrize(
    "base_image_tag, expected_image",
    (
        ("cuda", "bar"),
        (None, "foo"),
    ),
)
def test_make_run(_, base_image_tag, expected_image):
    @func(standalone=True, base_image_tag=base_image_tag)
    def foo():
        pass

    future = foo()

    with mock.patch(
        "sematic.runners.cloud_runner.CloudRunner._root_future",
        return_value=future,
    ):
        run = CloudRunner()._make_run(future)  # noqa: F811
        assert run.container_image_uri == expected_image


@mock.patch(
    "sematic.runners.cloud_runner.get_image_uris",
    return_value={"default": "foo", "cuda": "bar"},
)
@pytest.mark.parametrize(
    "detach, expected_status, expected_kind, _base_image_tag, expected_pipeline_run_container_image_uri",  # noqa: E501
    (
        (False, PipelineRunStatus.SCHEDULED, PipelineRunKind.LOCAL, "cuda", None),
        (True, PipelineRunStatus.CREATED, PipelineRunKind.KUBERNETES, "cuda", "bar"),
        (True, PipelineRunStatus.CREATED, PipelineRunKind.KUBERNETES, None, "foo"),
    ),
)
def test_make_pipeline_run(
    _,
    detach: bool,
    expected_status: PipelineRunStatus,
    expected_kind: PipelineRunKind,
    _base_image_tag: Optional[str],
    expected_pipeline_run_container_image_uri: Optional[str],
):
    @func
    def foo():
        pass

    future = foo()

    runner = (
        CloudRunner(detach=detach, _base_image_tag=_base_image_tag)
        if _base_image_tag
        else CloudRunner(detach=detach)
    )

    pipeline_run = runner._make_pipeline_run(future)

    assert pipeline_run.status == expected_status.value
    assert pipeline_run.kind == expected_kind.value
    assert pipeline_run.container_image_uris == {"default": "foo", "cuda": "bar"}
    assert pipeline_run.container_image_uri == expected_pipeline_run_container_image_uri


def test_runner_restart(
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
    persisted_resolution,  # noqa: F811
):
    # Emulate the state of a pipeline run which was partially
    # done already
    persisted_pipeline_run = persisted_resolution
    persisted_pipeline_run.status = PipelineRunStatus.RUNNING
    save_resolution(persisted_pipeline_run)

    @func
    def bar() -> int:
        return 1

    @func
    def foo() -> List[int]:
        child1 = bar()
        child2 = bar()
        child3 = bar()
        return [child1, child2, child3]

    root_run = get_run(persisted_pipeline_run.root_id)
    root_run.future_state = FutureState.RAN
    child_run1 = make_run(
        id="a" * 32,
        future_state=FutureState.RAN,
        parent_id=persisted_pipeline_run.root_id,
        root_id=persisted_pipeline_run.root_id,
    )
    child_run2 = make_run(
        id="b" * 32,
        future_state=FutureState.RESOLVED,
        parent_id=persisted_pipeline_run.root_id,
        root_id=persisted_pipeline_run.root_id,
    )
    child_run3 = make_run(
        id="c" * 32,
        future_state=FutureState.CREATED,
        parent_id=persisted_pipeline_run.root_id,
        root_id=persisted_pipeline_run.root_id,
    )
    child_run4 = make_run(
        id="d" * 32,
        future_state=FutureState.CREATED,
        parent_id=persisted_pipeline_run.root_id,
        root_id=persisted_pipeline_run.root_id,
    )
    runs = [root_run, child_run1, child_run2, child_run3, child_run4]

    edge1 = Edge(
        destination_run_id=child_run4.id,
        source_run_id=child_run1.id,
        destination_name="i0",
        artifact_id=None,
    )
    edge2 = Edge(
        destination_run_id=child_run4.id,
        source_run_id=child_run2.id,
        destination_name="i1",
        artifact_id=None,
    )
    edge3 = Edge(
        destination_run_id=child_run4.id,
        source_run_id=child_run3.id,
        destination_name="i2",
        artifact_id=None,
    )
    edges = [edge1, edge2, edge3]
    save_graph(runs=runs, artifacts=[], edges=edges)

    # Now that we have a partially executed pipeline run, see
    # what would happen if the runner restarted.
    future = foo()
    future.id = root_run.id
    future.state = FutureState[root_run.future_state]
    with environment_variables({"SEMATIC_CONTAINER_IMAGE": "foo:bar"}):
        with pytest.raises(Exception):
            InstrumentedCloudRunner(_is_running_remotely=True, detach=False).run(future)
    runs, _, __ = get_root_graph(root_run.id)
    read_run_state_by_id = {run.id: run.future_state for run in runs}  # noqa: F811
    assert read_run_state_by_id[child_run1.id] == FutureState.CANCELED.value
    assert read_run_state_by_id[child_run2.id] == FutureState.RESOLVED.value
    assert read_run_state_by_id[child_run3.id] == FutureState.CANCELED.value

    # We want the root run to show up as Failed in this circumstance.
    assert read_run_state_by_id[root_run.id] == FutureState.FAILED.value

    new_runner = _INSTRUMENTED_INSTANCES[-1]
    assert new_runner._run_called_with.function is future.function
    assert new_runner._run_called_with.kwargs == future.kwargs
    assert new_runner._run_called_with.id != future.id
    assert (
        new_runner._detach_pipeline_run_called_with.id == new_runner._run_called_with.id
    )
    assert new_runner._init_args[1]["rerun_from"] == root_run.id
    assert new_runner._init_args[1]["rerun_mode"] == RerunMode.CONTINUE
