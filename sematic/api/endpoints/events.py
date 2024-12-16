# Standard Library
import logging
from http import HTTPStatus
from typing import Any, Dict, Optional

# Third-party
import flask
import requests
from starlette.applications import Starlette  # type: ignore
from starlette.responses import JSONResponse  # type: ignore
from starlette.routing import Route  # type: ignore

# Sematic
from sematic import api_client
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate, authenticate_starlette
from sematic.db.models.user import User


logger = logging.getLogger(__name__)

_sio_server = None

_ROUTE = "/api/v1/events/<namespace>/<event>"
_STARLETTE_ROUTE = _ROUTE.replace("<", "{").replace(">", "}")


def register_sio_server(sio_server):
    global _sio_server
    if _sio_server is not None:
        raise RuntimeError("SocketIO Server already registered.")
    _sio_server = sio_server


@sematic_api.route(_ROUTE, methods=["POST"])
@authenticate
def sync_events(user: Optional[User], namespace: str, event: str) -> flask.Response:
    """
    Sends out a socketio broadcast notification to all subscribed listeners (Runners,
    the Dashboard, etc.).
    """
    logger.info("Broadcasting: namespace=%s; event=%s", namespace, event)
    logger.debug("Broadcasting: json payload=%s", flask.request.json)
    assert _sio_server is not None  # satisfy mypy

    _sio_server.emit(
        event,
        flask.request.json,
        namespace=f"/{namespace}",
    )

    return flask.jsonify({})


@authenticate_starlette
async def async_events(user: Optional[User], request):
    """
    Sends out a socketio broadcast notification to all subscribed listeners (Runners,
    the Dashboard, etc.).
    """
    namespace = request.path_params["namespace"]
    event = request.path_params["event"]
    request_json = await request.json()
    logger.info("Broadcasting: namespace=%s; event=%s", namespace, event)
    logger.debug("Broadcasting: json payload=%s", request_json)
    assert _sio_server is not None  # satisfy mypy

    await _sio_server.emit(
        event,
        request_json,
        namespace=f"/{namespace}",
    )

    return JSONResponse({})


async def health_check(request):
    return JSONResponse({})


starlette_app = Starlette(
    routes=[
        Route(_STARLETTE_ROUTE, async_events, methods=["POST"]),
        Route("/", health_check),
    ]
)


def broadcast_graph_update(
    root_id: str,
    user: Optional[User] = None,
) -> Optional[requests.Response]:
    url = "/events/graph/update"
    json_payload = dict(run_id=root_id)
    return _call_broadcast_endpoint(url=url, json_payload=json_payload, user=user)


def broadcast_resolution_cancel(
    root_id: str, function_path: str, user: Optional[User] = None
) -> Optional[requests.Response]:
    url = "/events/pipeline/cancel"
    json_payload = dict(resolution_id=root_id, function_path=function_path)
    return _call_broadcast_endpoint(url=url, json_payload=json_payload, user=user)


def broadcast_pipeline_update(
    function_path: str,
    user: Optional[User] = None,
) -> Optional[requests.Response]:
    url = "/events/pipeline/update"
    json_payload = dict(function_path=function_path)
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

    This is the endpoint where listeners have subscribed (Runners, the Dashboard, etc.).
    """
    logger.debug("Calling broadcast: url=%s; json_payload=%s", url, json_payload)

    try:
        response = api_client.request(
            method=requests.post,
            endpoint=url,
            kwargs=dict(json=json_payload),
            user=user,
            validate_version_compatibility=False,
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
