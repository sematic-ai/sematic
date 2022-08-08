# Standard library
from json import JSONDecodeError
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
import logging

# Third party
import requests

# Sematic
from sematic.versions import CURRENT_VERSION, version_as_string
from sematic.config import get_config
from sematic.user_settings import MissingSettingsError, SettingsVar, get_user_settings
from sematic.db.models.artifact import Artifact
from sematic.db.models.edge import Edge
from sematic.db.models.run import Run


logger = logging.getLogger(__name__)

# The client should always verify that it is compatible with the server
# it is talking to before using the API, but we don't want to do that every
# time. This caches whether we have validated it or not.
_validated_client_version = False


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


def notify_pipeline_update(calculator_path: str):
    _notify_event("pipeline", "update", {"calculator_path": calculator_path})


def notify_graph_update(run_id: str):
    _notify_event("graph", "update", {"run_id": run_id})


def _notify_event(namespace: str, event: str, payload: Any = None):
    _post("/events/{}/{}".format(namespace, event), payload)


def _get(endpoint) -> Any:
    response = _request(requests.get, endpoint)

    return response.json()


def _post(endpoint, json_payload) -> Any:
    response = _request(requests.post, endpoint, dict(json=json_payload))

    if len(response.content) == 0:
        return None

    return response.json()


def _put(endpoint, json_payload) -> Any:
    response = _request(requests.put, endpoint, dict(json=json_payload))

    if len(response.content) == 0:
        return None

    return response.json()


class APIConnectionError(requests.exceptions.ConnectionError):
    pass


class IncompatibleClientError(Exception):
    pass


class ServerError(Exception):
    pass


def _validate_server_compatibility(tries: int = 5, seconds_between_tries: int = 10):
    """Check that the client is compatible with the server.

    Raises an error if the server and client are incompatible, or if this can't be
    verified.
    """
    global _validated_client_version
    if _validated_client_version:
        return

    retriable_errors = (
        requests.exceptions.ConnectionError,
        ServerError,
    )
    response = None
    error = None
    for _ in range(tries):
        response, error = _validate_server_compatibility_no_catch()
        if error is None:
            _validated_client_version = True
            return
        if not isinstance(error, retriable_errors):
            break
        logger.warning(
            "Unsuccessful at determining version compatibility waiting %s seconds...",
            seconds_between_tries,
        )
        time.sleep(seconds_between_tries)
    if response is not None and response.status_code != 200:
        logger.error(
            "Sematic server returned status code %s when"
            " asked for version information. Response: %s",
            response.status_code,
            response.text,
        )
    raise error


def _validate_server_compatibility_no_catch() -> Tuple[
    Optional[requests.Response], Optional[Exception]
]:
    headers = {"Content-Type": "application/json"}
    response = None
    try:
        response = requests.get(_url("/meta/versions"), headers=headers)
    except requests.exceptions.ConnectionError:
        error = APIConnectionError(
            (
                f"Unable to connect to the Sematic API at "
                f"{get_config().server_url}.\n Make sure the "
                f"correct server address is set with\n"
                f"\t$ sematic settings set "
                f"{SettingsVar.SEMATIC_API_ADDRESS.value} <address>"
            )
        )
        return None, error
    unexpected_server_response_error = IncompatibleClientError(
        "The Sematic server did not provide information about its version "
        "in the expected format. It could be that the server is too old to "
        "provide this information. Consider upgrading your server if possible, "
        "or reach out to Sematic for support."
    )
    try:
        response_json = response.json()
    except JSONDecodeError:
        return response, unexpected_server_response_error
    if 400 <= response.status_code < 500:
        return response, unexpected_server_response_error
    if response.status_code >= 500:
        error = ServerError(
            f"The Sematic server is not responsive, and returned a status code of "
            f"{response.status_code}."
        )
        return response, error

    server_version = tuple(response_json["server"])
    server_min_client_version = tuple(response_json["min_client_supported"])
    if CURRENT_VERSION > server_version:
        error = IncompatibleClientError(
            f"The Sematic API client is at version "
            f"{version_as_string(CURRENT_VERSION)}, which is newer than "
            f"the Sematic server's version of "
            f"{version_as_string(server_version)}. Please downgrade your client "
            f"to {version_as_string(server_version)}, or ask your server admin "
            f"to upgrade to at least {version_as_string(CURRENT_VERSION)}."
        )
        return response, error
    if CURRENT_VERSION < server_min_client_version:
        error = IncompatibleClientError(
            f"The Sematic API client is at version "
            f"{version_as_string(CURRENT_VERSION)}, which is older than the "
            f"minimum version the server supports. Please upgrade your client "
            f"to a version of Sematic of at least "
            f"{version_as_string(server_min_client_version)}"
        )
        return response, error

    logger.info(
        "Sematic client %s is compatible with server %s",
        version_as_string(CURRENT_VERSION),
        version_as_string(server_version),
    )
    return response, None


def _request(
    method: Callable[[Any], requests.Response],
    endpoint: str,
    kwargs: Optional[Dict[str, Any]] = None,
):
    _validate_server_compatibility()
    kwargs = kwargs or {}

    headers = kwargs.get("headers", {})
    headers["Content-Type"] = "application/json"
    headers["X-API-KEY"] = _get_api_key()
    kwargs["headers"] = headers

    try:
        response = method(_url(endpoint), **kwargs)
    except requests.exceptions.ConnectionError:
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

    response.raise_for_status()

    return response


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
