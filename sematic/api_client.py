# Standard Library
import json
import logging
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, cast

# Third-party
import requests
from requests.exceptions import ConnectionError

# Sematic
from sematic.abstract_future import FutureState
from sematic.api.endpoints.auth import API_KEY_HEADER
from sematic.config.config import get_config
from sematic.config.settings import MissingSettingsError
from sematic.config.user_settings import UserSettings, UserSettingsVar, get_user_setting
from sematic.db.models.artifact import Artifact
from sematic.db.models.edge import Edge
from sematic.db.models.external_resource import ExternalResource
from sematic.db.models.factories import deserialize_artifact_value
from sematic.db.models.resolution import Resolution
from sematic.db.models.run import Run
from sematic.db.models.user import User
from sematic.plugins.abstract_external_resource import AbstractExternalResource
from sematic.utils.retry import retry
from sematic.versions import CURRENT_VERSION, version_as_string

logger = logging.getLogger(__name__)

# The client should always verify that it is compatible with the server
# it is talking to before using the API, but we don't want to do that every
# time. This caches whether we have validated it or not.
_validated_client_version = False


class APIConnectionError(ConnectionError):
    pass


class ServerError(Exception):
    pass


class InvalidResponseError(Exception):
    pass


class IncompatibleClientError(Exception):
    pass


class BadRequestError(Exception):
    pass


class ResourceNotFoundError(BadRequestError):
    pass


def get_artifact_value_by_id(artifact_id: str) -> Any:
    """
    Retrieve the value of an artifact by ID.

    Parameters
    ----------
    artifact_id: str
        The ID of the artifact.

    Returns
    -------
    Any:
        The value of the requested artifact.
    """
    artifact = _get_artifact(artifact_id)

    return get_artifact_value(artifact)


def get_artifact_value(artifact: Artifact) -> Any:
    payload = _get_artifact_bytes(artifact.id)

    return deserialize_artifact_value(artifact, payload)


def _get_artifact(artifact_id: str) -> Artifact:
    """
    Retrieve and deserialize artifact.
    """
    response = _get(f"/artifacts/{artifact_id}")

    return Artifact.from_json_encodable(response["content"])


@retry(tries=3, delay=10, jitter=1)
def store_artifact_bytes(artifact_id: str, bytes_: bytes) -> None:
    response = _get(f"/storage/artifacts/{artifact_id}/location")

    url: str = response["url"]
    headers: Dict[str, str] = response["request_headers"]

    requests.put(url, data=bytes_, headers=headers)


def _get_artifact_bytes(artifact_id: str) -> bytes:
    return _get(f"/storage/artifacts/{artifact_id}/data", decode_json=False)


def get_run(run_id: str) -> Run:
    """
    Get run
    """
    response = _get(f"/runs/{run_id}")

    return Run.from_json_encodable(response["content"])


def get_runs(
    limit: Optional[int] = None,
    order: Optional[Literal["asc", "desc"]] = None,
    **filters,
) -> List[Run]:
    """
    Get runs based on filter expressions.

    Parameters
    ----------
    limit: Optional[int]
        The maximum number of runs to return. Defaults to None.
    order: Optional[Literal["asc", "desc"]]
        Direction to order the `created_at` column by. Defaults to None, where it will
        sort in descending order.
    filters
        Column names and values by which to filter the runs. Defaults to empty dict.

    Returns
    -------
    A list of Runs which fit the filters.
    """
    # update this function whenever you need to add more query parameters
    query_filters = _get_encoded_query_filters(filters)
    query_string = f"/runs?limit={limit}&order={order}&filters={query_filters}"
    logger.debug("Fetching runs with query string: %s", query_string)

    response = _get(query_string)

    return [Run.from_json_encodable(run_result) for run_result in response["content"]]


def save_graph(
    root_id: str, runs: List[Run], artifacts: List[Artifact], edges: List[Edge]
):
    """
    Persist a graph.
    """
    payload = {
        "graph": {
            "runs": [run.to_json_encodable() for run in runs],
            "artifacts": [artifact.to_json_encodable() for artifact in artifacts],
            "edges": [edge.to_json_encodable() for edge in edges],
        }
    }

    _put("/graph", payload)
    notify_graph_update(root_id)


def get_graph(
    run_id: str, root: bool = False
) -> Tuple[List[Run], List[Artifact], List[Edge]]:
    """
    Get a graph for a run.

    This will return only the run's direct edges and artifacts

    Parameters
    ----------
    run_id: str
        The ID whose graph to retrieve

    root: bool
        Defaults to `False`. If `True`, `run_id` is presumed to be a root run's ID
        and the whole graph is retrieved. If `False`, only the immediate graph around
        the run is retrieved (i.e. immediate edges and their artifacts).
    """
    response = _get(f"/runs/{run_id}/graph?root={int(root)}")

    runs = [Run.from_json_encodable(run) for run in response["runs"]]
    artifacts = [
        Artifact.from_json_encodable(artifact) for artifact in response["artifacts"]
    ]
    edges = [Edge.from_json_encodable(edge) for edge in response["edges"]]

    return runs, artifacts, edges


def save_resolution(resolution: Resolution):
    payload = {
        "resolution": resolution.to_json_encodable(),
    }
    _put(f"/resolutions/{resolution.root_id}", payload)


def get_resolution(root_id: str) -> Resolution:
    """
    Get resolution
    """
    response = _get(f"/resolutions/{root_id}")

    return Resolution.from_json_encodable(response["content"])


def cancel_resolution(resolution_id: str) -> Resolution:
    response = _put(f"/resolutions/{resolution_id}/cancel", {})

    return Resolution.from_json_encodable(response["content"])


def schedule_run(run_id: str) -> Run:
    """Ask the server to execute the calculator for the run."""
    response = _post(f"/runs/{run_id}/schedule", json_payload={})
    return Run.from_json_encodable(response["content"])


def schedule_resolution(
    resolution_id: str,
    max_parallelism: Optional[int] = None,
    rerun_from: Optional[str] = None,
) -> Resolution:
    """Ask the server to start a detached resolution execution."""
    payload: Dict[str, Any] = {}

    if max_parallelism is not None:
        payload["max_parallelism"] = max_parallelism

    if rerun_from is not None:
        payload["rerun_from"] = rerun_from

    response = _post(f"/resolutions/{resolution_id}/schedule", json_payload=payload)
    return Resolution.from_json_encodable(response["content"])


def save_external_resource(
    resource: AbstractExternalResource,
) -> AbstractExternalResource:
    """Save the external resource to the server, return the result.

    Parameters
    ----------
    resource:
        The resource to save.

    Returns
    -------
    The resource as saved by the server.
    """
    record = ExternalResource.from_resource(resource)
    payload = {"external_resource": record.to_json_encodable()}
    response = _post("/external_resources", json_payload=payload)
    return ExternalResource.from_json_encodable(response["external_resource"]).resource


def get_external_resource(
    resource_id: str, refresh_remote: bool
) -> AbstractExternalResource:
    """Get the external resource, updating the status if required.

    Will actively interact with the external resource if necessary to get its status.

    Parameters
    ----------
    resource_id:
        The id of the resource to retrieve.
    refresh_remote:
        If true: refresh the state of the resource with the remote objects it represents.
        Locally managed objects will NOT have their state refreshed. If False, the
        external resource will be returned directly from the DB.

    Returns
    -------
    The latest update of the external resource.
    """
    response = _get(
        f"/external_resources/{resource_id}?refresh_remote={str(refresh_remote).lower()}"
    )
    return ExternalResource.from_json_encodable(response["external_resource"]).resource


def activate_external_resource(resource_id: str) -> AbstractExternalResource:
    """Activate the external resource on the server, return the result.

    Parameters
    ----------
    resource_id:
        The id of the resource to activate.

    Returns
    -------
    The resource as saved by the server.
    """
    response = _post(f"/external_resources/{resource_id}/activate", json_payload={})
    return ExternalResource.from_json_encodable(response["external_resource"]).resource


def deactivate_external_resource(resource_id: str) -> AbstractExternalResource:
    """Deactivate the external resource on the server, return the result.

    Parameters
    ----------
    resource_id:
        The id of the resource to deactivate.

    Returns
    -------
    The resource as saved by the server.
    """
    response = _post(f"/external_resources/{resource_id}/deactivate", json_payload={})
    return ExternalResource.from_json_encodable(response["external_resource"]).resource


def save_resource_run_links(resource_ids: List[str], run_id: str) -> None:
    """Save that the run with the given id is using the resource with the given id.

    Parameters
    ----------
    resource_ids:
        The ids of the resources to record a link for.
    run_id:
        The id of the run to record a link for.
    """
    _post(
        f"/runs/{run_id}/external_resources",
        json_payload={"external_resource_ids": resource_ids},
    )


def get_resources_by_root_run_id(root_run_id: str) -> List[AbstractExternalResource]:
    """Get a list of external resources associated with the given root run.

    Parameters
    ----------
    root_run_id:
        The id of the root run of a resolution.

    Returns
    -------
    A list of external resources used by runs underneath the specified root run.
    """
    response = _get(f"/resolutions/{root_run_id}/external_resources")
    return [
        ExternalResource.from_json_encodable(resource).resource
        for resource in response["external_resources"]
    ]


@retry(tries=3, delay=10, jitter=1)
def update_run_future_states(run_ids: List[str]) -> Dict[str, FutureState]:
    """Ask the server to update the status of given run ids if needed and return them.

    The server will actively update run statuses based on the state of remote jobs
    associated with the runs.

    Parameters
    ----------
    run_ids:
        The ids of the runs whose statuses are being requested

    Returns
    -------
    A dict whose keys are run ids and whose values are the current state of the runs.
    """
    response = _post("/runs/future_states", json_payload={"run_ids": run_ids})
    result_dict = {}
    for run_result in response["content"]:
        result_dict[run_result["run_id"]] = FutureState[run_result["future_state"]]
    return result_dict


def notify_pipeline_update(calculator_path: str):
    _notify_event("pipeline", "update", {"calculator_path": calculator_path})


def notify_graph_update(run_id: str):
    _notify_event("graph", "update", {"run_id": run_id})


def _notify_event(namespace: str, event: str, payload: Any = None):
    logger.debug(
        "Notifying update: namespace=%s; event=%s; payload=%s",
        namespace,
        event,
        payload,
    )
    _post("/events/{}/{}".format(namespace, event), payload)


@retry(
    exceptions=(ServerError, APIConnectionError),
    tries=4,
    delay=1,
    backoff=2,
    jitter=0.1,
)
def _get(endpoint: str, decode_json: bool = True) -> Any:
    """
    Get a payload from the API server.

    Parameters
    ----------
    endpoint: str
        Endpoint to query. `/api/v1` will be prepended and authentication
        headers will be added.
    decode_json: bool
        Defaults to `True`. Whether the returned payload should be JSON-decoded.
    """
    response = request(requests.get, endpoint)
    logger.debug("Got response with raw content: %s", response.content)

    if decode_json:
        return response.json()

    return response.content


@retry(
    exceptions=APIConnectionError,
    tries=4,
    delay=1,
    backoff=2,
    jitter=0.1,
)
def _post(endpoint, json_payload) -> Any:
    response = request(requests.post, endpoint, dict(json=json_payload))

    if len(response.content) == 0:
        return None

    return response.json()


@retry(
    exceptions=APIConnectionError,
    tries=4,
    delay=1,
    backoff=2,
    jitter=0.1,
)
def _put(
    endpoint: str,
    json_payload: Optional[Dict[str, Any]] = None,
    data: Optional[bytes] = None,
) -> Any:
    response = request(requests.put, endpoint, dict(json=json_payload, data=data))

    if len(response.content) == 0:
        return None

    return response.json()


def _validate_server_compatibility(
    tries: int = 5, seconds_between_tries: int = 10, use_cached: bool = True
):
    """Check that the client is compatible with the server.

    Raises an error if the server and client are incompatible, or if this can't be
    verified.
    """
    global _validated_client_version
    if _validated_client_version and use_cached:
        return

    retriable_errors = (
        ConnectionError,
        ServerError,
    )
    retry(
        exceptions=retriable_errors,
        tries=tries,
        delay=seconds_between_tries,
    )(_validate_server_compatibility_no_catch)()

    _validated_client_version = True


def _validate_server_compatibility_no_catch() -> None:
    base_url = get_config().api_url.replace("/api/v1", "")
    unexpected_server_response_error = IncompatibleClientError(
        "The Sematic server did not provide information about its version "
        "in the expected format. Most likely this means that your "
        "SEMATIC_API_ADDRESS is pointing to a URL which resolves to something other "
        "than your Sematic deployment. Please verify your deployment by running the "
        "following curl command. The response should be html with a '🦊' emoji in it. "
        "If it is not, please correct your Sematic deployment, networking or "
        "SEMATIC_API_ADDRESS so that you can reach it from this host. "
        f"CURL COMMAND: \n\n\tcurl {base_url}\n"
    )

    try:
        response = request(
            method=requests.get,
            endpoint="/meta/versions",
            attempt_auth=False,
            validate_version_compatibility=False,  # to avoid recursion
            validate_json=True,
        )
    except (BadRequestError, InvalidResponseError):
        raise unexpected_server_response_error
    except ServerError:
        raise ServerError("The Sematic server is not responsive")

    response_json = response.json()
    server_version = cast(Tuple[int, int, int], tuple(response_json["server"]))
    server_min_client_version = cast(
        Tuple[int, int, int], tuple(response_json["min_client_supported"])
    )
    if CURRENT_VERSION > server_version:
        raise IncompatibleClientError(
            f"The Sematic API client is at version "
            f"{version_as_string(CURRENT_VERSION)}, which is newer than "
            f"the Sematic server's version of "
            f"{version_as_string(server_version)}. Please downgrade your client "
            f"to {version_as_string(server_version)}, or ask your server admin "
            f"to upgrade to at least {version_as_string(CURRENT_VERSION)}."
        )
    if CURRENT_VERSION < server_min_client_version:
        raise IncompatibleClientError(
            f"The Sematic API client is at version "
            f"{version_as_string(CURRENT_VERSION)}, which is older than the "
            f"minimum version the server supports. Please upgrade your client "
            f"to a version of Sematic of at least "
            f"{version_as_string(server_min_client_version)}"
        )

    logger.debug(
        "Sematic client %s is compatible with server %s",
        version_as_string(CURRENT_VERSION),
        version_as_string(server_version),
    )


def request(
    method: Callable[[Any], requests.Response],
    endpoint: str,
    kwargs: Optional[Dict[str, Any]] = None,
    attempt_auth: bool = True,
    validate_version_compatibility: bool = True,
    validate_json: bool = False,
    user: Optional[User] = None,
):
    """Internal function for wrapping requests.<get/put/etc.>.

    validate_version_compatibility indicates whether we should check that the
    Sematic server is compatible with this Sematic client.

    validate_json indicates whether the response is expected to contain
    valid json.
    """
    if validate_version_compatibility:
        _validate_server_compatibility()
    kwargs = kwargs or {}

    headers = kwargs.get("headers", {})
    headers["Content-Type"] = "application/json"
    if attempt_auth:
        headers[API_KEY_HEADER] = _get_api_key(user)

    kwargs["headers"] = headers

    try:
        response = method(_url(endpoint), **kwargs)
    except ConnectionError:
        raise APIConnectionError(
            (
                f"Unable to connect to the Sematic API at {get_config().server_url}.\n"
                f"Make sure the correct server address is set with\n"
                f"\t$ sematic settings set {UserSettingsVar.SEMATIC_API_ADDRESS.value} "
                f"<address>"
            )
        )

    if (
        response.status_code == requests.codes.unauthorized
        and headers[API_KEY_HEADER] is None
    ):
        raise MissingSettingsError(UserSettings, UserSettingsVar.SEMATIC_API_KEY)

    _raise_for_response(
        response,
        validate_json,
    )

    return response


def _raise_for_response(
    response: requests.Response,
    validate_json: bool,
) -> None:
    exception: Optional[Exception] = None
    url, method = response.url, response.request.method

    if response.status_code == 404:
        exception = ResourceNotFoundError(f"Resource {url} was not found")

    elif 400 <= response.status_code < 500:
        exception = BadRequestError(
            f"The {method} request to {url} was invalid, "
            f"response was {response.status_code}"
        )

    elif response.status_code >= 500:
        exception = ServerError(
            f"The Sematic server could not handle the " f"{method} request to {url}",
        )

    if exception is None and validate_json:
        try:
            response.json()
        except Exception:
            exception = InvalidResponseError(
                f"The Sematic server was expected to return json for "
                f"{method} request to {url}, but the "
                f"response was not json."
            )

    if exception is None:
        return

    logger.error(
        "Server returned %s for %s %s: %s",
        response.status_code,
        method,
        url,
        response.text,
    )
    raise exception


def _url(endpoint: str) -> str:
    # we send socket.io notifications to a dedicated address, if configured
    if endpoint.startswith("/events/"):
        url = f"{get_config().socket_io_url}{endpoint}"
        logger.debug("Constructed socketio url: %s", url)
    else:
        url = f"{get_config().api_url}{endpoint}"
        logger.debug("Constructed server url: %s", url)

    return url


def _get_api_key(user: Optional[User] = None) -> Optional[str]:
    """
    Read the API key from user settings.

    If a User dataclass is passed, then the key is taken from its fields. If not, then
    the key is taken from the user settings.
    """
    if user is not None and user.api_key is not None:
        return user.api_key
    try:
        return get_user_setting(UserSettingsVar.SEMATIC_API_KEY)
    except MissingSettingsError:
        return None


def _get_encoded_query_filters(filters: Dict[str, Any]) -> str:
    """
    Returns the encoded "filters" parameter value that can be given to `_request` from a
    freeform key-value dict.
    """
    if len(filters) == 1:
        col = next(iter(filters))
        return json.dumps({col: {"eq": filters[col]}})

    if len(filters) > 1:
        return json.dumps({"AND": [{col: {"eq": filters[col]}} for col in filters]})

    return json.dumps(None)
