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
from sematic.calculator import func
from sematic.db.models.factories import make_artifact
from sematic.db.models.resolution import ResolutionKind, ResolutionStatus
from sematic.db.queries import get_root_graph, get_run, save_resolution, save_run
from sematic.db.tests.fixtures import make_run  # noqa: F401
from sematic.db.tests.fixtures import persisted_resolution  # noqa: F401
from sematic.db.tests.fixtures import persisted_run  # noqa: F401
from sematic.db.tests.fixtures import pg_mock  # noqa: F401
from sematic.db.tests.fixtures import run  # noqa: F401
from sematic.db.tests.fixtures import (  # noqa: F401
    allow_any_run_state_transition,
    test_db,
)
from sematic.resolvers.cloud_resolver import CloudResolver
from sematic.tests.fixtures import (  # noqa: F401
    environment_variables,
    valid_client_version,
)


@func(base_image_tag="cuda", inline=False)
def add(a: float, b: float) -> float:
    return a + b


# TODO: support pipeline args
@func
def pipeline() -> float:
    return add(1, 2)


@mock.patch("sematic.api_client.update_run_future_states")
@mock.patch("sematic.resolvers.cloud_resolver.get_image_uris")
@mock.patch("sematic.api_client.schedule_run")
@mock.patch("sematic.api_client.schedule_resolution")
@mock.patch("kubernetes.config.load_kube_config")
def test_simulate_cloud_exec(
    mock_load_kube_config: mock.MagicMock,
    mock_schedule_resolution: mock.MagicMock,
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
    resolver = CloudResolver(detach=True)

    future = pipeline()
    images = {
        "default": "default_image",
        "cuda": "cuda_image",
    }
    mock_get_images.return_value = images

    result = future.resolve(resolver)
    add_run_ids = []

    assert result == future.id

    def fake_schedule(run_id):
        if run_id == future.id:
            raise RuntimeError("Root future should not need scheduling--it's inline!")
        run = api_client.get_run(run_id)  # noqa: F811
        if "add" in run.calculator_path:
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
            edge = driver_resolver._get_output_edges(run.id)[0]
            artifact, bytes_ = make_artifact(3, int)
            edge.artifact_id = artifact.id
            api_client.save_graph(
                run.id, runs=[run], artifacts=[artifact], edges=[edge]
            )
            api_client.store_artifact_bytes(artifact.id, bytes_)
            driver_resolver._refresh_graph(run.id)
        return updates

    mock_update_run_future_states.side_effect = fake_update_run_future_states

    mock_schedule_resolution.assert_called_once_with(
        resolution_id=future.id, max_parallelism=None, rerun_from=None
    )
    assert api_client.get_resolution(future.id).status == ResolutionStatus.CREATED.value

    resolution = api_client.get_resolution(future.id)
    root_run = api_client.get_run(future.id)
    assert root_run.container_image_uri == images["default"]
    resolution.status = ResolutionStatus.SCHEDULED
    api_client.save_resolution(resolution)
    mock_schedule_run.assert_not_called()

    # In the driver job

    runs, artifacts, edges = api_client.get_graph(future.id)

    driver_resolver = CloudResolver(detach=False, _is_running_remotely=True)

    driver_resolver.set_graph(runs=runs, artifacts=artifacts, edges=edges)
    assert (
        api_client.get_resolution(future.id).status == ResolutionStatus.SCHEDULED.value
    )
    output = driver_resolver.resolve(future)

    assert output == 3
    assert (
        api_client.get_resolution(future.id).status == ResolutionStatus.COMPLETE.value
    )
    assert mock_get_images.call_count == 1
    assert driver_resolver._get_tagged_image("cuda") == images["cuda"]
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
        CloudResolver(max_parallelism=max_parallelism)
    except ValueError:
        assert not expected_validates
        return
    assert expected_validates


@mock.patch(
    "sematic.resolvers.cloud_resolver.get_image_uris",
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
    @func(inline=False, base_image_tag=base_image_tag)
    def foo():
        pass

    future = foo()

    with mock.patch(
        "sematic.resolvers.cloud_resolver.CloudResolver._root_future",
        return_value=future,
    ):
        run = CloudResolver()._make_run(future)  # noqa: F811
        assert run.container_image_uri == expected_image


@mock.patch(
    "sematic.resolvers.cloud_resolver.get_image_uris",
    return_value={"default": "foo", "cuda": "bar"},
)
@pytest.mark.parametrize(
    "detach, expected_status, expected_kind, _base_image_tag, expected_resolution_container_image_uri",  # noqa: E501
    (
        (False, ResolutionStatus.SCHEDULED, ResolutionKind.LOCAL, "cuda", None),
        (True, ResolutionStatus.CREATED, ResolutionKind.KUBERNETES, "cuda", "bar"),
        (True, ResolutionStatus.CREATED, ResolutionKind.KUBERNETES, None, "foo"),
    ),
)
def test_make_resolution(
    _,
    detach: bool,
    expected_status: ResolutionStatus,
    expected_kind: ResolutionKind,
    _base_image_tag: Optional[str],
    expected_resolution_container_image_uri: Optional[str],
):
    @func
    def foo():
        pass

    future = foo()

    resolver = (
        CloudResolver(detach=detach, _base_image_tag=_base_image_tag)
        if _base_image_tag
        else CloudResolver(detach=detach)
    )

    resolution = resolver._make_resolution(future)

    assert resolution.status == expected_status.value
    assert resolution.kind == expected_kind.value
    assert resolution.container_image_uris == {"default": "foo", "cuda": "bar"}
    assert resolution.container_image_uri == expected_resolution_container_image_uri


def test_resolver_restart(
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    test_db,  # noqa: F811
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
    persisted_resolution,  # noqa: F811
):
    # Emulate the state of a resolution which was partially
    # done already
    persisted_resolution.status = ResolutionStatus.RUNNING
    save_resolution(persisted_resolution)

    @func
    def bar() -> int:
        return 1

    @func
    def foo() -> List[int]:
        child1 = bar()
        child2 = bar()
        child3 = bar()
        return [child1, child2, child3]

    root_run = get_run(persisted_resolution.root_id)
    root_run.future_state = FutureState.RAN
    child_run1 = make_run(
        future_state=FutureState.RAN,
        parent_id=persisted_resolution.root_id,
        root_id=persisted_resolution.root_id,
    )
    child_run2 = make_run(
        future_state=FutureState.RESOLVED,
        parent_id=persisted_resolution.root_id,
        root_id=persisted_resolution.root_id,
    )
    child_run3 = make_run(
        future_state=FutureState.CREATED,
        parent_id=persisted_resolution.root_id,
        root_id=persisted_resolution.root_id,
    )
    for run in [root_run, child_run1, child_run2, child_run3]:  # noqa: F402
        save_run(run)

    # Now that we have a partially executed resolution, see
    # what would happen if the resolver restarted.
    future = foo()
    future.id = root_run.id
    with environment_variables({"SEMATIC_CONTAINER_IMAGE": "foo:bar"}):
        with pytest.raises(Exception):
            CloudResolver(_is_running_remotely=True, detach=False).resolve(future)
    runs, _, __ = get_root_graph(root_run.id)
    read_run_state_by_id = {run.id: run.future_state for run in runs}
    assert read_run_state_by_id[child_run1.id] == FutureState.CANCELED.value
    assert read_run_state_by_id[child_run2.id] == FutureState.RESOLVED.value
    assert read_run_state_by_id[child_run3.id] == FutureState.CANCELED.value
    assert read_run_state_by_id[root_run.id] == FutureState.CANCELED.value
