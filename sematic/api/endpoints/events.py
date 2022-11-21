# Standard Library
from typing import Optional

# Third-party
import flask
import flask_socketio  # type: ignore

# Sematic
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate
from sematic.db.models.user import User


@sematic_api.route("/api/v1/events/<namespace>/<event>", methods=["POST"])
@authenticate
def events(user: Optional[User], namespace: str, event: str) -> flask.Response:
    flask_socketio.emit(
        event,
        flask.request.json,
        namespace="/{}".format(namespace),
        broadcast=True,
    )
    return flask.jsonify({})


def broadcast_graph_update(root_id: str) -> None:
    flask_socketio.emit(
        "update",
        dict(run_id=root_id),
        namespace="/graph",
        broadcast=True,
    )


def broadcast_resolution_cancel(root_id: str, calculator_path: str) -> None:
    flask_socketio.emit(
        "cancel",
        dict(resolution_id=root_id, calculator_path=calculator_path),
        namespace="/pipeline",
        broadcast=True,
    )


def broadcast_pipeline_update(calculator_path: str) -> None:
    flask_socketio.emit(
        "update",
        dict(calculator_path=calculator_path),
        namespace="/pipeline",
        broadcast=True,
    )
