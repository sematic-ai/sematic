"""
Functions to generate models.
"""
# Standard Library
import datetime
import json
import secrets
from typing import Any, List, Optional, Tuple

# Sematic
from sematic.abstract_future import AbstractFuture, FutureState, make_future_id
from sematic.db.models.artifact import Artifact
from sematic.db.models.edge import Edge
from sematic.db.models.resolution import Resolution, ResolutionStatus
from sematic.db.models.run import Run
from sematic.db.models.user import User
from sematic.storage import Storage
from sematic.types.serialization import (
    get_json_encodable_summary,
    type_from_json_encodable,
    type_to_json_encodable,
    value_from_json_encodable,
    value_to_json_encodable,
)
from sematic.types.types.union import get_value_type, is_union
from sematic.utils.hashing import get_value_and_type_sha1_digest
from sematic.utils.json import fix_nan_inf


def make_run_from_future(future: AbstractFuture) -> Run:
    """
    Create a Run model instance from a future.
    """
    run = Run(
        id=future.id,
        original_run_id=future.original_future_id,
        future_state=future.state,
        name=future.props.name,
        calculator_path=make_func_path(future),
        parent_id=(
            future.parent_future.id if future.parent_future is not None else None
        ),
        nested_future_id=(
            future.nested_future.id if future.nested_future is not None else None
        ),
        description=future.calculator.__doc__,
        tags=future.props.tags,
        source_code=future.calculator.get_source(),
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow(),
        cache_key=None,
    )

    # Set this outside the constructor because the constructor expects
    # a json encodable, but this property will auto-update the json
    # encodable field.
    run.resource_requirements = future.props.resource_requirements

    return run


def clone_root_run(run: Run, edges: List[Edge]) -> Tuple[Run, List[Edge]]:
    """
    Clone a root run and its edges.

    Parameters
    ----------
    run: Run
        Original run to clone.
    edges: List[Edge]
        Original run's input and output edges.

    Returns
    -------
    Tuple[Run, List[Edge]]
        A tuple whose first element is the cloned run, and the second element is
        the list of cloned edges.
    """
    run_id = make_future_id()
    cloned_run = Run(
        id=run_id,
        original_run_id=run.original_run_id,
        root_id=run_id,
        future_state=FutureState.CREATED,
        name=run.name,
        calculator_path=run.calculator_path,
        parent_id=None,
        description=run.description,
        tags=run.tags,
        source_code=run.source_code,
        container_image_uri=run.container_image_uri,
        cache_key=run.cache_key,
    )

    # Set this outside the constructor because the constructor expects
    # a json encodable, but this property will auto-update the json
    # encodable field.
    cloned_run.resource_requirements = run.resource_requirements

    cloned_edges = [
        Edge(
            destination_run_id=(run_id if edge.destination_run_id == run.id else None),
            source_run_id=(run_id if edge.source_run_id == run.id else None),
            destination_name=edge.destination_name,
            artifact_id=edge.artifact_id,
        )
        for edge in edges
    ]

    return cloned_run, cloned_edges


def clone_resolution(resolution: Resolution, root_id: str) -> Resolution:
    """
    Clone a resolution.

    Parameters
    ----------
    resolution: Resolution
        Original resolution to clone.
    root_id: str
        The root ID for this resolution. Typically comes from the cloned root
        run.

    Returns
    -------
    Resolution
        Cloned resolution.
    """
    cloned_resolution = Resolution(
        root_id=root_id,
        status=ResolutionStatus.CREATED,
        kind=resolution.kind,
        settings_env_vars=resolution.settings_env_vars,
        container_image_uri=resolution.container_image_uri,
        container_image_uris=resolution.container_image_uris,
        client_version=resolution.client_version,
        cache_namespace=resolution.cache_namespace,
    )

    # Set this outside the constructor because the constructor expects
    # a json encodable, but this property will auto-update the json
    # encodable field.
    cloned_resolution.git_info = resolution.git_info

    return cloned_resolution


def make_func_path(future: AbstractFuture) -> str:
    return f"{future.calculator.__module__}.{future.calculator.__name__}"


def make_artifact(
    value: Any, type_: Any, storage: Optional[Storage] = None
) -> Artifact:
    """
    Create an Artifact model instance from a value and type.
    """
    if is_union(type_):
        type_ = get_value_type(value, type_)
    type_serialization = type_to_json_encodable(type_)
    value_serialization = value_to_json_encodable(value, type_)
    json_summary = get_json_encodable_summary(value, type_)

    artifact = Artifact(
        id=get_value_and_type_sha1_digest(
            value_serialization, type_serialization, json_summary
        ),
        json_summary=fix_nan_inf(json.dumps(json_summary, sort_keys=True, default=str)),
        type_serialization=json.dumps(type_serialization, sort_keys=True),
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow(),
    )

    if storage is not None:
        storage.set(
            _make_artifact_storage_key(artifact),
            json.dumps(value_serialization, sort_keys=True).encode("utf-8"),
        )

    return artifact


def get_artifact_value(artifact: Artifact, storage: Storage) -> Any:
    """
    Fetch artifact serialization from storage and deserialize.
    """
    payload = storage.get(_make_artifact_storage_key(artifact))

    value_serialization = json.loads(payload.decode("utf-8"))
    type_serialization = json.loads(artifact.type_serialization)

    type_ = type_from_json_encodable(type_serialization)

    value = value_from_json_encodable(value_serialization, type_)

    return value


def _make_artifact_storage_key(artifact: Artifact) -> str:
    return "artifacts/{}".format(artifact.id)


def make_user(
    email: str,
    first_name: Optional[str],
    last_name: Optional[str],
    avatar_url: Optional[str],
) -> User:
    """
    Make a user
    """
    api_key = _make_api_key()

    return User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        avatar_url=avatar_url,
        api_key=api_key,
    )


def _make_api_key() -> str:
    """
    Generate an API key
    """
    return secrets.token_urlsafe(16)
