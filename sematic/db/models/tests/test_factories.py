# Standard Library
import hashlib
import json

# Third-party
import pytest

# Sematic
from sematic.abstract_future import FutureState
from sematic.calculator import func
from sematic.db.models.edge import Edge
from sematic.db.models.factories import (
    _make_artifact_storage_key,
    clone_resolution,
    clone_root_run,
    get_artifact_value,
    make_artifact,
    make_run_from_future,
)
from sematic.db.models.resolution import Resolution, ResolutionStatus
from sematic.db.models.run import Run
from sematic.db.tests.fixtures import resolution, run  # noqa: F401
from sematic.plugins.storage.memory_storage import MemoryStorage
from sematic.resolvers.resource_requirements import (
    KubernetesResourceRequirements,
    ResourceRequirements,
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
    assert run.calculator_path == "sematic.db.models.tests.test_factories.f"
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
    artifact = make_artifact(42, int)

    value_serialization = value_to_json_encodable(42, int)
    type_serialization = type_to_json_encodable(int)
    json_summary = get_json_encodable_summary(42, int)

    payload = {
        "value": value_serialization,
        "type": type_serialization,
        "summary": json_summary,
    }

    sha1 = hashlib.sha1(json.dumps(payload, sort_keys=True).encode("utf-8"))

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
    artifact = make_artifact(value, float)

    assert json.loads(artifact.json_summary) == expected_value


def test_make_artifact_store():
    storage = MemoryStorage()
    artifact = make_artifact(42, int, storage=storage)

    storage_key = _make_artifact_storage_key(artifact)

    assert storage.get(storage_key) == "42".encode("utf-8")


def test_get_artifact_value():
    storage = MemoryStorage()
    artifact = make_artifact(42, int, storage=storage)

    value = get_artifact_value(artifact, storage)

    assert value == 42
    assert isinstance(value, int)


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
    assert cloned_run.calculator_path == run.calculator_path
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
    assert cloned_edges[2].artifact_id == "ghi789"


def test_clone_resolution(resolution: Resolution):  # noqa: F811
    cloned_resolution = clone_resolution(resolution, root_id="abc123")

    assert cloned_resolution.root_id == "abc123"
    assert cloned_resolution.status is ResolutionStatus.CREATED.value
    assert cloned_resolution.kind is resolution.kind
    assert cloned_resolution.git_info == resolution.git_info
    assert cloned_resolution.settings_env_vars == resolution.settings_env_vars
    assert cloned_resolution.container_image_uri == resolution.container_image_uri
    assert cloned_resolution.container_image_uris == resolution.container_image_uris
