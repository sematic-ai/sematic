"""
Functions to generate models.
"""

# Standard Library
import datetime
import enum
import json
import secrets
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

# Sematic
from sematic.abstract_future import AbstractFuture, FutureState, make_future_id
from sematic.db.models.artifact import Artifact
from sematic.db.models.edge import Edge
from sematic.db.models.job import Job
from sematic.db.models.organization import Organization
from sematic.db.models.organization_user import OrganizationUser
from sematic.db.models.resolution import Resolution, ResolutionStatus
from sematic.db.models.run import Run
from sematic.db.models.user import User
from sematic.resolvers.type_utils import make_list_type, make_tuple_type
from sematic.scheduling.job_details import JobDetails, JobKindString, JobStatus
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
    # Note: when updating this you likely need to also update
    # initialize_future_from_run below.
    run = Run(
        id=future.id,
        original_run_id=future.original_future_id,
        future_state=future.state,
        name=future.props.name,
        function_path=make_func_path(future),
        parent_id=(future.parent_future.id if future.parent_future is not None else None),
        nested_future_id=(
            future.nested_future.id if future.nested_future is not None else None
        ),
        description=future.function.__doc__,
        tags=future.props.tags,
        source_code=future.function.get_source(),
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow(),
        cache_key=None,
        # the user_id is overwritten on the API call based on the user's API key
        user_id=None,
    )

    # Set this outside the constructor because the constructor expects
    # a json encodable, but this property will auto-update the json
    # encodable field.
    run.resource_requirements = future.props.resource_requirements

    return run


def initialize_future_from_run(
    run: Run, kwargs: Dict[str, Any], use_same_id: bool = True
) -> AbstractFuture:
    """Initialize a future using corresponding properties in the run.

    Only properties that are completely represented
    in the run itself or its corresponding Sematic Function arguments will
    be set. In particular, properties requiring access to a broader run graph
    or external sources of information will NOT be updated by this function.
    It is thus primarily useful in conjunction with something constructing
    futures with access to a full run graph (ex: see graph.py).

    A list (not necessarily exhaustive) of fields that will explicitly
    NOT be updated on the future from the run, due to lack of broader
    graph access or other listed reasons:

    - resolved_kwargs: requires full graph access
    - value: requires full graph access
    - parent_future: requires full graph access
    - nested_future: requires full graph access
    - standalone: May be set by the run's function; see Issue #1032
    - cache: May be set by the run's function; see Issue #1032
    - timeout_mins: May be set by the run's function; see Issue #1032
    - retry_settings: May be set by the run's function; see Issue #1032

    Parameters
    ----------
    run:
        The run to update properties from.
    kwargs:
        The keyword arguments for the future.
    use_same_id:
        Whether the new future should have the same id as the provided run.
        Defaults to True.

    Returns
    -------
    A future created from the given run.
    """
    # Note: when updating this you likely need to also update
    # make_run_from_future above.
    func = run.get_func()

    # _make_list and _make_tuple need special treatment as they are not
    # decorated functions, but factories that dynamically generate futures.
    if run.function_path == "sematic.function._make_list":
        # Dict values insertion order guaranteed as of Python 3.7
        input_list = list(kwargs.values())
        future = func(make_list_type(input_list), input_list)  # type: ignore
    elif run.function_path == "sematic.function._make_tuple":
        # Dict values insertion order guaranteed as of Python 3.7
        input_tuple = tuple(kwargs.values())
        future = func(make_tuple_type(input_tuple), input_tuple)  # type: ignore
    else:
        future = func(**kwargs)

    if use_same_id:
        future.id = run.id
    future.props.name = run.name
    future.props.tags = json.loads(str(run.tags))
    future_state = run.future_state
    if isinstance(future_state, str):
        future_state = FutureState[future_state]
    future.props.state = future_state
    future.props.resource_requirements = run.resource_requirements
    if run.started_at is not None:
        future.props.scheduled_epoch_time = run.started_at.timestamp()

    return future


def clone_root_run(
    run: Run, edges: List[Edge], artifacts_override: Optional[Dict[str, str]] = None
) -> Tuple[Run, List[Edge]]:
    """
    Clone a root run and its edges.

    Parameters
    ----------
    run: Run
        Original run to clone.
    edges: List[Edge]
        Original run's input and output edges.
    artifacts_override: Optional[Dict[str, str]]
        A mapping between Function parameter names and Artifact ids. Used to overwrite the
        original Run Artifact ids in the cloned Run, in order to produce reruns with
        different input Artifacts. Defaults to None, meaning rerunning with the same
        inputs.

    Returns
    -------
    Tuple[Run, List[Edge]]
        A tuple whose first element is the cloned run, and the second element is
        the list of cloned edges.
    """
    artifacts_override = artifacts_override or {}

    run_id = make_future_id()
    cloned_run = Run(
        id=run_id,
        original_run_id=run.original_run_id,
        root_id=run_id,
        future_state=FutureState.CREATED,
        name=run.name,
        function_path=run.function_path,
        parent_id=None,
        description=run.description,
        tags=run.tags,
        source_code=run.source_code,
        container_image_uri=run.container_image_uri,
        cache_key=run.cache_key,
        # the user_id is overwritten on the API call based on the user's API key
        user_id=None,
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
            artifact_id=(
                artifacts_override.get(edge.destination_name, edge.artifact_id)
                # the output artifact MUST be reset
                if edge.destination_name is not None
                else None
            ),
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
        # the user_id is overwritten on the API call based on the user's API key
        user_id=None,
        run_command=resolution.run_command,
        build_config=resolution.build_config,
    )

    # Set this outside the constructor because the constructor expects
    # a json encodable, but this property will auto-update the json
    # encodable field.
    cloned_resolution.git_info = resolution.git_info
    cloned_resolution.resource_requirements = resolution.resource_requirements

    return cloned_resolution


def make_job(
    name: str,
    namespace: str,
    run_id: str,
    status: JobStatus,
    details: JobDetails,
    kind: JobKindString,
) -> Job:
    """Make a new Job using the given status and details.

    Parameters
    ----------
    name:
        The name of the K8s job.
    namespace:
        The namespace of the K8s job.
    run_id:
        The id of the run the job is associated with.
    status:
        The status of the job.
    details:
        Details about the job.
    kind:
        Whether the job is for a resolution or a run.
    """
    return Job(
        name=name,
        namespace=namespace,
        run_id=run_id,
        last_updated_epoch_seconds=status.last_updated_epoch_seconds,
        state=status.state,
        kind=kind,
        message=status.message,
        detail_serialization=asdict(details),
        status_history_serialization=[asdict(status)],
    )


def make_func_path(future: AbstractFuture) -> str:
    return f"{future.function.__module__}.{future.function.__name__}"


class StorageNamespace(enum.Enum):
    artifacts = "artifacts"
    futures = "futures"
    blobs = "blobs"


@dataclass
class UploadPayload:
    namespace: StorageNamespace
    key: str
    payload: bytes


def make_artifact(value: Any, type_: Any) -> Tuple[Artifact, Tuple[UploadPayload, ...]]:
    """
    Create an Artifact model instance from a value and type.
    """
    if is_union(type_):
        type_ = get_value_type(value, type_)

    type_serialization = type_to_json_encodable(type_)
    value_serialization = value_to_json_encodable(value, type_)
    json_summary, blobs = get_json_encodable_summary(value, type_)

    artifact_id = get_value_and_type_sha1_digest(
        value_serialization, type_serialization, json_summary
    )

    artifact = Artifact(
        id=artifact_id,
        json_summary=fix_nan_inf(json.dumps(json_summary, sort_keys=True, default=str)),
        type_serialization=json.dumps(type_serialization, sort_keys=True),
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow(),
    )

    payload = json.dumps(value_serialization, sort_keys=True).encode("utf-8")

    upload_payloads = [
        UploadPayload(
            namespace=StorageNamespace.artifacts, key=artifact_id, payload=payload
        )
    ]
    for key, blob in blobs.items():
        upload_payloads.append(
            UploadPayload(namespace=StorageNamespace.blobs, key=key, payload=blob)
        )

    return artifact, tuple(upload_payloads)


def deserialize_artifact_value(artifact: Artifact, payload: bytes) -> Any:
    """
    Deserialize serialized artifact value.
    """
    value_serialization = json.loads(payload.decode("utf-8"))
    type_serialization = json.loads(artifact.type_serialization)

    type_ = type_from_json_encodable(type_serialization)

    value = value_from_json_encodable(value_serialization, type_)

    return value


def make_user(
    email: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    avatar_url: Optional[str] = None,
) -> User:
    """
    Make a user.
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


def make_personal_organization(user: User) -> Tuple[Organization, OrganizationUser]:
    """
    Makes a personal organization for the user, as well as the membership & admin
    relationship between the two.

    The user is expected to have an `id` field, meaning the entry was flushed to the DB.
    """

    organization = Organization(
        id=user.id, name=user.get_friendly_name(), kubernetes_namespace=None
    )
    organization_user = OrganizationUser(
        organization_id=organization.id, user_id=user.id, admin=True
    )
    return organization, organization_user
