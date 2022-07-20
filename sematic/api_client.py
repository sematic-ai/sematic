# Standard library
from typing import Any, Callable, Dict, List, Optional, Tuple
import logging

# Third party
import requests

# Sematic
from sematic.config import get_config
from sematic.user_settings import SettingsVar
from sematic.db.models.artifact import Artifact
from sematic.db.models.edge import Edge
from sematic.db.models.run import Run


logger = logging.getLogger(__name__)


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


def _request(
    method: Callable[[Any], requests.Response],
    endpoint: str,
    kwargs: Optional[Dict[str, Any]] = None,
):
    try:
        response = method(_url(endpoint), **(kwargs or {}))
    except requests.exceptions.ConnectionError:
        raise APIConnectionError(
            (
                "Unable to connect to the Sematic API at {}.\n"
                "Make sure the correct server address is set with\n"
                "\t$ sematic settings set {} <address>"
            ).format(get_config().server_url, SettingsVar.SEMATIC_API_ADDRESS.value)
        )

    response.raise_for_status()

    return response


def _url(endpoint) -> str:
    return "{}{}".format(get_config().api_url, endpoint)
