# Standard Library
import logging
from typing import Optional

# Third-party
import flask
import flask_socketio  # type: ignore
import requests

# Sematic
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate
from sematic.config.config import get_config
from sematic.db.models.user import User

logger = logging.getLogger(__name__)


@sematic_api.route("/api/v1/events/<namespace>/<event>", methods=["POST"])
@authenticate
def events(user: Optional[User], namespace: str, event: str) -> flask.Response:
    logger.error("Broadcasting: namespace=%s; event=%s", namespace, event)
    flask_socketio.emit(
        event,
        flask.request.json,
        namespace="/{}".format(namespace),
        broadcast=True,
    )
    return flask.jsonify({})


def broadcast_graph_update(root_id: str) -> None:
    url = f"{get_config().socket_io_url}/events/graph/update"
    logger.error("Calling broadcast: run_id=%s; url=%s", root_id, url)
    requests.post(url, json=dict(run_id=root_id))

    # flask_socketio.emit(
    #     "update",
    #     dict(run_id=root_id),
    #     namespace="/graph",
    #     broadcast=True,
    # )


def broadcast_resolution_cancel(root_id: str, calculator_path: str) -> None:
    url = f"{get_config().socket_io_url}/events/pipeline/cancel"
    logger.error("Calling broadcast: resolution_id=%s; url=%s", root_id, url)
    requests.post(url, json=dict(resolution_id=root_id, calculator_path=calculator_path))

    # flask_socketio.emit(
    #     "cancel",
    #     dict(resolution_id=root_id, calculator_path=calculator_path),
    #     namespace="/pipeline",
    #     broadcast=True,
    # )


def broadcast_pipeline_update(calculator_path: str) -> None:
    url = f"{get_config().socket_io_url}/events/pipeline/update"
    logger.error("Calling broadcast: calculator_path=%s; url=%s", calculator_path, url)
    requests.post(url, json=dict(calculator_path=calculator_path))

    # flask_socketio.emit(
    #     "update",
    #     dict(calculator_path=calculator_path),
    #     namespace="/pipeline",
    #     broadcast=True,
    # )
