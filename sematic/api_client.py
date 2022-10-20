# Standard Library
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, cast

# Third party
import requests
from requests.exceptions import ConnectionError

# Sematic
from sematic.abstract_future import FutureState
from sematic.config import get_config
from sematic.db.models.artifact import Artifact
from sematic.db.models.edge import Edge
from sematic.db.models.factories import get_artifact_value
from sematic.db.models.resolution import Resolution
from sematic.db.models.run import Run
from sematic.user_settings import MissingSettingsError, SettingsVar, get_user_settings
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


def get_artifact_value_by_id(artifact_id: str) -> Any:
    """
    Retrieve the value of an artifact by ID.

    Parameters
    ----------
    artifact_id: str

    Returns
    -------
    Any
        The value of the requiested artifact.
    """
    artifact = _get_artifact(artifact_id)
    return get_artifact_value(artifact)


def _get_artifact(artifact_id: str) -> Artifact:
    """
    Retrieve and deserialize artifact.
    """
    response = _get("/artifacts/{}".format(artifact_id))

    return Artifact.from_json_encodable(response["content"])


def get_run(run_id: str) -> Run:
    """
    Get run
    """
    response = _get("/runs/{}".format(run_id))

    return Run.from_json_encodable(response["content"])


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


def get_graph(run_id: str) -> Tuple[List[Run], List[Artifact], List[Edge]]:
    """
    Get a graph for a run.

    This will return only the run's direct edges and artifacts
    TODO: implement root=True option to get all graph for root, not needed currently.
    """
    response = _get("/runs/{}/graph".format(run_id))

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
    response = _get("/resolutions/{}".format(root_id))

    return Resolution.from_json_encodable(response["content"])


def cancel_resolution(resolution_id: str) -> Resolution:
    response = _put(f"/resolutions/{resolution_id}/cancel", {})

    return Resolution.from_json_encodable(response["content"])


def schedule_run(run_id: str) -> Run:
    """Ask the server to execute the calculator for the run."""
    response = _post(f"/runs/{run_id}/schedule", json_payload={})
    return Run.from_json_encodable(response["content"])


def schedule_resolution(resolution_id: str) -> Resolution:
    """Ask the server to start a detached resolution execution."""
    response = _post(f"/resolutions/{resolution_id}/schedule", json_payload={})
    return Resolution.from_json_encodable(response["content"])


@retry(tries=3, delay=10, jitter=1)
def update_run_future_states(run_ids: List[str]) -> Dict[str, FutureState]:
    """Ask the server to update the status of given run ids if needed and return them.

    The server will actively update run statuses based on the state of remote jobs
    associated with the runs. It will NOT perform any updates to the run statuses
    that result from result availability or calculator errors.

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
    _post("/events/{}/{}".format(namespace, event), payload)


@retry(
    exceptions=(ServerError, APIConnectionError),
    tries=4,
    delay=1,
    backoff=2,
    jitter=0.1,
)
def _get(endpoint) -> Any:
    response = _request(requests.get, endpoint)

    return response.json()


@retry(
    exceptions=APIConnectionError,
    tries=4,
    delay=1,
    backoff=2,
    jitter=0.1,
)
def _post(endpoint, json_payload) -> Any:
    response = _request(requests.post, endpoint, dict(json=json_payload))

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
def _put(endpoint, json_payload) -> Any:
    response = _request(requests.put, endpoint, dict(json=json_payload))

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
        response = _request(
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


def _request(
    method: Callable[[Any], requests.Response],
    endpoint: str,
    kwargs: Optional[Dict[str, Any]] = None,
    attempt_auth: bool = True,
    validate_version_compatibility: bool = True,
    validate_json: bool = False,
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
        headers["X-API-KEY"] = _get_api_key()
    kwargs["headers"] = headers

    try:
        response = method(_url(endpoint), **kwargs)
    except ConnectionError:
        raise APIConnectionError(
            (
                "Unable to connect to the Sematic API at {}.\n"
                "Make sure the correct server address is set with\n"
                "\t$ sematic settings set {} <address>"
            ).format(get_config().server_url, SettingsVar.SEMATIC_API_ADDRESS.value)
        )

    if (
        response.status_code == requests.codes.unauthorized
        and headers["X-API-KEY"] is None
    ):
        raise MissingSettingsError(SettingsVar.SEMATIC_API_KEY)

    _raise_for_response(
        response,
        validate_json,
    )

    return response


def _raise_for_response(
    response: requests.Response,
    validate_json: bool,
) -> None:
    to_raise: Optional[Exception] = None
    url = response.url
    error_4xx = BadRequestError(
        f"The {response.request.method} request to {url} was invalid, "
        f"response was {response.status_code}"
    )
    error_5xx = ServerError(
        f"The Sematic server could not handle the "
        f"{response.request.method} request to {url}",
    )

    if 400 <= response.status_code < 500:
        to_raise = error_4xx
    if response.status_code >= 500:
        to_raise = error_5xx
    if to_raise is None and validate_json:
        try:
            response.json()
        except Exception:
            to_raise = InvalidResponseError(
                f"The Sematic server was expected to return json for "
                f"{response.request.method} request to {url}, but the "
                f"response was not json."
            )
    if to_raise is None:
        return

    logger.error(
        "Server returned %s for %s %s: %s",
        response.status_code,
        response.request.method,
        url,
        response.text,
    )
    raise to_raise


def _url(endpoint) -> str:
    return "{}{}".format(get_config().api_url, endpoint)


def _get_api_key() -> Optional[str]:
    """
    Read the API key from user settings.
    """
    try:
        return get_user_settings(SettingsVar.SEMATIC_API_KEY)
    except MissingSettingsError:
        return None
