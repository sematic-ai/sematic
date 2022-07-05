# Standard library
from typing import Any, List

# Third party
import requests

# Sematic
from sematic.config import get_config
from sematic.db.models.artifact import Artifact
from sematic.db.models.edge import Edge
from sematic.db.models.run import Run


def save_graph(runs: List[Run], artifacts: List[Artifact], edges: List[Edge]):
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


def notify_pipeline_update(calculator_path: str):
    _notify_event("pipeline", "update", {"calculator_path": calculator_path})


def notify_graph_update(run_id: str):
    _notify_event("graph", "update", {"run_id": run_id})


def _notify_event(namespace: str, event: str, payload: Any = None):
    _post("/events/{}/{}".format(namespace, event), payload)


def _post(endpoint, json_payload) -> Any:
    url = _url(endpoint)
    response = requests.post(url, json=json_payload)
    response.raise_for_status()

    if len(response.content) == 0:
        return None

    return response.json()


def _put(endpoint, json_payload) -> Any:
    url = _url(endpoint)
    response = requests.put(url, json=json_payload)
    response.raise_for_status()

    if len(response.content) == 0:
        return None

    return response.json()


def _url(endpoint) -> str:
    return "{}{}".format(get_config().api_url, endpoint)
