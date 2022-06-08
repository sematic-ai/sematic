# Third-party
import argparse
from flask import jsonify, send_file
from flask_socketio import SocketIO  # type: ignore

# Sematic
from sematic.api.app import sematic_api

# Endpoint modules need to be imported for endpoints
# to be registered.
import sematic.api.endpoints.runs  # noqa: F401
import sematic.api.endpoints.edges  # noqa: F401
import sematic.api.endpoints.artifacts  # noqa: F401
from sematic.config import (
    DEFAULT_ENV,
    get_config,
    switch_env,
)  # noqa: F401


@sematic_api.route("/")
@sematic_api.route("/<path:path>")
def index(path=""):
    """
    Returns the index page of the UI app.

    To build the UI app:
    $ cd ui
    $ npm run build
    """
    return send_file("../ui/build/index.html")


@sematic_api.route("/api/v1/ping")
def ping():
    """
    Basic health ping. Does not include DB liveness check.
    """
    return jsonify({"status": "ok"})


socketio = SocketIO(sematic_api)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser("Sematic API server")
    parser.add_argument("--env", required=False, default=DEFAULT_ENV, type=str)
    parser.add_argument("--debug", required=False, default=False, action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    switch_env(args.env)

    sematic_api.debug = args.debug

    socketio.run(sematic_api, port=get_config().port, host=get_config().server_address)
