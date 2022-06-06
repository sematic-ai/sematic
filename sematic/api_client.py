# Standard library
from typing import Any

# Third party
import requests

# Sematic
from sematic.config import get_config


def notify_pipeline_start(calculator_path: str):
    _notify_event("pipeline", "start", {"calculator_path": calculator_path})


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


def _url(endpoint) -> str:
    return "{}{}".format(get_config().api_url, endpoint)
