# Third-party
from flask import jsonify
from flask_socketio import SocketIO  # type: ignore

# Glow
from glow.api.app import glow_api

# Endpoint modules need to be imported for endpoints
# to be registered.
import glow.api.endpoints.runs  # noqa: F401
import glow.api.endpoints.edges  # noqa: F401
import glow.api.endpoints.artifacts  # noqa: F401


@glow_api.route("/")
def index():
    return jsonify({"hello": "world"})


@glow_api.route("/api/v1/ping")
def ping():
    """
    Basic health ping. Does not include DB liveness check.
    """
    return jsonify({"status": "ok"})


socketio = SocketIO(glow_api)

if __name__ == "__main__":
    glow_api.debug = True
    # glow_api.run(debug=True)
    socketio.run(glow_api)
