# Standard Library
import hashlib
import json
import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Union

# Third-party
import pytest

# Sematic
from sematic.abstract_future import FutureState
from sematic.db.models.edge import Edge
from sematic.db.models.factories import (
    clone_resolution,
    clone_root_run,
    initialize_future_from_run,
    make_artifact,
    make_job,
    make_run_from_future,
)
from sematic.db.models.job import Job
from sematic.db.models.resolution import Resolution, ResolutionStatus
from sematic.db.models.run import Run
from sematic.db.tests.fixtures import resolution, run  # noqa: F401
from sematic.function import func
from sematic.resolvers.resource_requirements import (
    KubernetesResourceRequirements,
    ResourceRequirements,
)
from sematic.scheduling.job_details import (
    JobDetails,
    JobKind,
    JobStatus,
    KubernetesJobState,
)
from sematic.types.serialization import (
    get_json_encodable_summary,
    type_to_json_encodable,
    value_to_json_encodable,
)


@func
def f():
    """
    An informative docstring.
    """
    pass  # Some note


@func
def f2(a: int, b: int) -> int:
    return a + b


def test_make_run_from_future():
    future = f()
    parent_future = f()
    future.parent_future = parent_future
    resource_reqs = ResourceRequirements(
        kubernetes=KubernetesResourceRequirements(
            node_selector={"foo": "bar"},
        )
    )
    future.props.resource_requirements = resource_reqs
    run = make_run_from_future(future)  # noqa: F811

    assert run.id == future.id
    assert run.future_state == FutureState.CREATED.value
    assert run.function_path == "sematic.db.models.tests.test_factories.f"
    assert run.name == "f"
    assert run.parent_id == parent_future.id
    assert run.description == "An informative docstring."
    assert isinstance(run.resource_requirements, ResourceRequirements)
    assert run.resource_requirements.kubernetes.node_selector == {"foo": "bar"}
    assert (
        run.source_code
        == """@func
def f():
    \"\"\"
    An informative docstring.
    \"\"\"
    pass  # Some note
"""
    )


def test_make_artifact():
    artifact, _ = make_artifact(42, int)

    value_serialization = value_to_json_encodable(42, int)
    type_serialization = type_to_json_encodable(int)
    json_summary, blobs = get_json_encodable_summary(42, int)

    payload = {
        "value": value_serialization,
        "type": type_serialization,
        "summary": json_summary,
    }

    sha1 = hashlib.sha1(json.dumps(payload, sort_keys=True).encode("utf-8"))

    assert blobs == {}
    assert artifact.id == sha1.hexdigest()
    assert artifact.json_summary == json.dumps(json_summary, sort_keys=True)
    assert artifact.type_serialization == json.dumps(type_serialization, sort_keys=True)


def test_make_artifact_with_optional_type_hint():
    artifact, _ = make_artifact([42], Optional[List[int]])

    value_serialization = value_to_json_encodable([42], List[int])
    type_serialization = type_to_json_encodable(List[int])
    json_summary, blobs = get_json_encodable_summary([42], List[int])

    payload = {
        "value": value_serialization,
        "type": type_serialization,
        "summary": json_summary,
    }

    sha1 = hashlib.sha1(json.dumps(payload, sort_keys=True).encode("utf-8"))

    assert blobs == {}
    assert artifact.id == sha1.hexdigest()
    assert artifact.json_summary == json.dumps(json_summary, sort_keys=True)
    assert artifact.type_serialization == json.dumps(type_serialization, sort_keys=True)


def test_make_artifact_with_nested_union_type_hint():
    artifact, _ = make_artifact([42], Union[Union[List[int], str], List[str]])

    value_serialization = value_to_json_encodable([42], List[int])
    type_serialization = type_to_json_encodable(List[int])
    json_summary, blobs = get_json_encodable_summary([42], List[int])

    payload = {
        "value": value_serialization,
        "type": type_serialization,
        "summary": json_summary,
    }

    sha1 = hashlib.sha1(json.dumps(payload, sort_keys=True).encode("utf-8"))

    assert blobs == {}
    assert artifact.id == sha1.hexdigest()
    assert artifact.json_summary == json.dumps(json_summary, sort_keys=True)
    assert artifact.type_serialization == json.dumps(type_serialization, sort_keys=True)


@pytest.mark.parametrize(
    "value, expected_value",
    (
        (float("nan"), "NaN"),
        (float("Infinity"), "Infinity"),
        (float("-Infinity"), "-Infinity"),
    ),
)
def test_make_artifact_special_floats(value, expected_value):
    artifact, _ = make_artifact(value, float)

    assert json.loads(artifact.json_summary) == expected_value


def test_clone_root_run(run: Run):  # noqa: F811
    edges = [
        Edge(destination_run_id=run.id, destination_name="foo", artifact_id="abc123"),
        Edge(destination_run_id=run.id, destination_name="bar", artifact_id="def456"),
        Edge(source_run_id=run.id, artifact_id="ghi789"),
    ]

    cloned_run, cloned_edges = clone_root_run(run, edges)

    assert cloned_run.id != run.id
    assert cloned_run.root_id == cloned_run.id
    assert cloned_run.future_state is FutureState.CREATED.value
    assert cloned_run.name == run.name
    assert cloned_run.function_path == run.function_path
    assert cloned_run.parent_id is None
    assert cloned_run.description is not None
    assert cloned_run.description == run.description
    assert cloned_run.tags == run.tags
    assert cloned_run.source_code is not None
    assert cloned_run.source_code == run.source_code
    assert cloned_run.container_image_uri is not None
    assert cloned_run.container_image_uri == run.container_image_uri
    assert cloned_run.resource_requirements is not None
    assert cloned_run.resource_requirements == run.resource_requirements

    assert cloned_edges[0].destination_run_id == cloned_run.id
    assert cloned_edges[0].source_run_id is None
    assert cloned_edges[0].destination_name == "foo"
    assert cloned_edges[0].artifact_id == "abc123"

    assert cloned_edges[1].destination_run_id == cloned_run.id
    assert cloned_edges[1].source_run_id is None
    assert cloned_edges[1].destination_name == "bar"
    assert cloned_edges[1].artifact_id == "def456"

    assert cloned_edges[2].destination_run_id is None
    assert cloned_edges[2].source_run_id == cloned_run.id
    assert cloned_edges[2].artifact_id is None


def test_clone_root_run_artifacts_override(run: Run):  # noqa: F811
    edges = [
        Edge(destination_run_id=run.id, destination_name="foo", artifact_id="abc123"),
        Edge(destination_run_id=run.id, destination_name="bar", artifact_id="def456"),
        Edge(source_run_id=run.id, artifact_id="ghi789"),
    ]

    cloned_run, cloned_edges = clone_root_run(
        run=run, edges=edges, artifacts_override={"foo": "jkl123"}
    )

    assert cloned_run.id != run.id
    assert cloned_run.root_id == cloned_run.id
    assert cloned_run.future_state is FutureState.CREATED.value
    assert cloned_run.name == run.name
    assert cloned_run.function_path == run.function_path
    assert cloned_run.parent_id is None
    assert cloned_run.description is not None
    assert cloned_run.description == run.description
    assert cloned_run.tags == run.tags
    assert cloned_run.source_code is not None
    assert cloned_run.source_code == run.source_code
    assert cloned_run.container_image_uri is not None
    assert cloned_run.container_image_uri == run.container_image_uri
    assert cloned_run.resource_requirements is not None
    assert cloned_run.resource_requirements == run.resource_requirements

    assert cloned_edges[0].destination_run_id == cloned_run.id
    assert cloned_edges[0].source_run_id is None
    assert cloned_edges[0].destination_name == "foo"
    assert cloned_edges[0].artifact_id == "jkl123"

    assert cloned_edges[1].destination_run_id == cloned_run.id
    assert cloned_edges[1].source_run_id is None
    assert cloned_edges[1].destination_name == "bar"
    assert cloned_edges[1].artifact_id == "def456"

    assert cloned_edges[2].destination_run_id is None
    assert cloned_edges[2].source_run_id == cloned_run.id
    assert cloned_edges[2].artifact_id is None


def test_clone_resolution(resolution: Resolution):  # noqa: F811
    cloned_resolution = clone_resolution(resolution, root_id="abc123")

    assert cloned_resolution.root_id == "abc123"
    assert cloned_resolution.status is ResolutionStatus.CREATED.value
    assert cloned_resolution.kind is resolution.kind
    assert cloned_resolution.git_info == resolution.git_info
    assert cloned_resolution.settings_env_vars == resolution.settings_env_vars
    assert cloned_resolution.container_image_uri == resolution.container_image_uri
    assert cloned_resolution.container_image_uris == resolution.container_image_uris
    assert cloned_resolution.client_version == resolution.client_version
    assert cloned_resolution.cache_namespace == resolution.cache_namespace
    assert cloned_resolution.user_id == resolution.user_id
    assert cloned_resolution.run_command == resolution.run_command
    assert cloned_resolution.build_config == resolution.build_config


def test_initialize_future_from_run():
    created_at = datetime(year=2023, month=8, day=10, tzinfo=timezone(timedelta(hours=4)))
    run = Run(  # noqa: F811
        id="theid",
        original_run_id=None,
        future_state=FutureState.RAN,
        name="the name",
        function_path=f"{f2.__module__}.{f2.__name__}",
        parent_id="parentid",
        root_id="rootid",
        description="the description",
        tags=["foo", "bar"],
        nested_future_id="nestedid",
        container_image_uri="imageuri",
        created_at=created_at,
        updated_at=created_at + timedelta(hours=2),
        started_at=created_at + timedelta(hours=1),
        ended_at=created_at + timedelta(2),
        resolved_at=created_at + timedelta(2),
        failed_at=None,
        cache_key="cachekey",
    )
    requirements = ResourceRequirements(
        kubernetes=KubernetesResourceRequirements(
            node_selector={"foo": "bar"},
        )
    )
    run.resource_requirements = requirements

    kwargs = {"a": 1, "b": 2}
    future = initialize_future_from_run(run, kwargs=kwargs, use_same_id=True)

    assert future.id == run.id
    assert future.function is f2
    assert future.props.name == run.name
    assert future.props.tags == json.loads(run.tags)  # type: ignore
    assert future.props.state == FutureState[run.future_state]  # type: ignore
    assert future.props.resource_requirements == requirements
    assert future.props.scheduled_epoch_time == 1691614800
    assert future.kwargs == kwargs

    future2 = initialize_future_from_run(run, kwargs, use_same_id=False)
    assert future2.id != future.id

    run.function_path = "sematic.function._make_list"
    future3 = initialize_future_from_run(run, kwargs={"v0": 0, "v1": 1})
    assert future3.function.execute(**future3.kwargs) == [0, 1]


def test_new():
    name = "foo"
    namespace = "bar"
    run_id = "abc123"
    job_kind = JobKind.run
    status = JobStatus(
        state=KubernetesJobState.Requested,
        message="Just created",
        last_updated_epoch_seconds=time.time(),
    )
    details = JobDetails(
        try_number=0,
    )
    job = make_job(
        name=name,
        namespace=namespace,
        run_id=run_id,
        status=status,
        details=details,
        kind=job_kind,
    )
    assert isinstance(job, Job)

    assert job.name == name
    assert job.namespace == namespace
    assert job.run_id == run_id
    assert job.last_updated_epoch_seconds == status.last_updated_epoch_seconds
    assert job.state == status.state
    assert job.kind == job_kind
    assert job.message == status.message
    assert job.details == details
    assert job.status_history == (status,)
