# Standard Library
import logging
from typing import Optional

# Third-party
import flask
import flask_socketio  # type: ignore
import requests

# Sematic
from sematic import api_client
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate
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


def broadcast_graph_update(
    root_id: str, user: Optional[User] = None,
) -> requests.Response:
    # url = f"{get_config().socket_io_url}/events/graph/update"
    url = "/events/graph/update"
    logger.error("Calling broadcast: run_id=%s; url=%s", root_id, url)
    json_payload = dict(run_id=root_id)
    return api_client._request(
        method=requests.post, endpoint=url, kwargs=dict(json=json_payload), user=user
    )

    # flask_socketio.emit(
    #     "update",
    #     dict(run_id=root_id),
    #     namespace="/graph",
    #     broadcast=True,
    # )


def broadcast_resolution_cancel(
    root_id: str, calculator_path: str, user: Optional[User] = None
) -> requests.Response:
    # url = f"{get_config().socket_io_url}/events/pipeline/cancel"
    url = "/events/pipeline/cancel"
    logger.error("Calling broadcast: resolution_id=%s; url=%s", root_id, url)
    json_payload = dict(resolution_id=root_id, calculator_path=calculator_path)
    return api_client._request(
        method=requests.post, endpoint=url, kwargs=dict(json=json_payload), user=user
    )

    # flask_socketio.emit(
    #     "cancel",
    #     dict(resolution_id=root_id, calculator_path=calculator_path),
    #     namespace="/pipeline",
    #     broadcast=True,
    # )


def broadcast_pipeline_update(
    calculator_path: str, user: Optional[User] = None,
) -> requests.Response:
    # url = f"{get_config().socket_io_url}/events/pipeline/update"
    url = "/events/pipeline/update"
    logger.error("Calling broadcast: calculator_path=%s; url=%s", calculator_path, url)
    json_payload = dict(calculator_path=calculator_path)
    return api_client._request(
        method=requests.post, endpoint=url, kwargs=dict(json=json_payload), user=user
    )

    # flask_socketio.emit(
    #     "update",
    #     dict(calculator_path=calculator_path),
    #     namespace="/pipeline",
    #     broadcast=True,
    # )
