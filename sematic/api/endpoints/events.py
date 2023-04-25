# Standard Library
import logging
from http import HTTPStatus
from typing import Any, Dict, Optional

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
    """
    Sends out a socketio broadcast notification to all subscribed listeners (Resolvers,
    the Dashboard, etc.).
    """
    logger.info("Broadcasting: namespace=%s; event=%s", namespace, event)
    logger.debug("Broadcasting: json payload=%s", flask.request.json)

    flask_socketio.emit(
        event,
        flask.request.json,
        namespace="/{}".format(namespace),
        broadcast=True,
    )

    return flask.jsonify({})


def broadcast_graph_update(
    root_id: str,
    user: Optional[User] = None,
) -> Optional[requests.Response]:
    url = "/events/graph/update"
    json_payload = dict(run_id=root_id)
    return _call_broadcast_endpoint(url=url, json_payload=json_payload, user=user)


def broadcast_resolution_cancel(
    root_id: str, calculator_path: str, user: Optional[User] = None
) -> Optional[requests.Response]:
    url = "/events/pipeline/cancel"
    json_payload = dict(resolution_id=root_id, calculator_path=calculator_path)
    return _call_broadcast_endpoint(url=url, json_payload=json_payload, user=user)


def broadcast_pipeline_update(
    calculator_path: str,
    user: Optional[User] = None,
) -> Optional[requests.Response]:
    url = "/events/pipeline/update"
    json_payload = dict(calculator_path=calculator_path)
    return _call_broadcast_endpoint(url=url, json_payload=json_payload, user=user)


def broadcast_job_update(
    run_id: str,
    user: Optional[User] = None,
) -> Optional[requests.Response]:
    url = "/events/job/update"
    json_payload = dict(run_id=run_id)
    return _call_broadcast_endpoint(url=url, json_payload=json_payload, user=user)


def _call_broadcast_endpoint(
    url: str, json_payload: Dict[str, Any], user: Optional[User] = None
) -> Optional[requests.Response]:
    """
    Calls the endpoint that can send out a socketio broadcast notification.

    This is the endpoint where listeners have subscribed (Resolvers, the Dashboard, etc.).
    """
    logger.debug("Calling broadcast: url=%s; json_payload=%s", url, json_payload)

    try:
        response = api_client.request(
            method=requests.post,
            endpoint=url,
            kwargs=dict(json=json_payload),
            user=user,
        )
    except Exception:
        logger.exception("Unable to broadcast event")
        return None

    if response.status_code == HTTPStatus.OK:
        return response

    logger.error(
        "Unable to broadcast event - HTTP %s: %s",
        response.status_code,
        response.content,
    )
    return None
