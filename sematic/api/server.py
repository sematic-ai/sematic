if __name__ == "__main__":
    # Third-party
    import gevent.monkey  # type: ignore

    # This enables us to use websockets and standard HTTP requests in
    # the same server locally, which is what we want. If you try to
    # use Gunicorn to do this, gevent will complain about
    # not monkey patching early enough, unless you have the gevent
    # monkey patch applied VERY early (like user/sitecustomize).
    # Monkey patching: https://github.com/gevent/gevent/issues/1235
    gevent.monkey.patch_all()

# Standard Library
import argparse
import logging
import os
import signal
import sys
from logging.config import dictConfig
from typing import Optional

# Third-party
import flask
from flask import jsonify, send_file
from flask_socketio import Namespace, SocketIO  # type: ignore

# Sematic
# Endpoint modules need to be imported for endpoints
# to be registered.
import sematic.api.endpoints.artifacts  # noqa: F401
import sematic.api.endpoints.auth  # noqa: F401
import sematic.api.endpoints.edges  # noqa: F401
import sematic.api.endpoints.events  # noqa: F401
import sematic.api.endpoints.external_resources  # noqa: F401
import sematic.api.endpoints.meta  # noqa: F401
import sematic.api.endpoints.notes  # noqa: F401
import sematic.api.endpoints.resolutions  # noqa: F401
import sematic.api.endpoints.runs  # noqa: F401
import sematic.api.endpoints.storage  # noqa: F401
import sematic.api.endpoints.users  # noqa: F401
from sematic.api.app import sematic_api
from sematic.api.wsgi import SematicWSGI
from sematic.config.config import get_config, switch_env  # noqa: F401
from sematic.config.settings import import_plugins
from sematic.logs import make_log_config

# Some plugins may register endpoints
import_plugins()


_logger: Optional[logging.Logger] = None


def logger() -> logging.Logger:
    """Lazy-init and return a logger object"""
    # lazy-init is necessary because the logger must be instantiated
    # after the logging config is handled, and that can happen in an
    # app run thread if we are using a WSGI server. In that case we don't
    # have an easy "hook" to init the logger after the WSGI app has
    # done its log config initialization.
    global _logger
    if _logger is None:
        _logger = logging.getLogger(__name__)
    return _logger


@sematic_api.route("/data/<file>")
def data(file: str):
    """
    Endpoint to serve images and large payloads stored on disc.
    """
    path = os.path.join(get_config().data_dir, file)
    return send_file(path)


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


def _request_string(request) -> str:
    query_string = (
        f"?{str(request.query_string, encoding='utf8')}"
        if len(request.query_string) > 0
        else ""
    )
    request_string = (
        f"{request.remote_addr} {request.user_agent} "
        f"{request.method} {request.path}{query_string}"
    )
    return request_string


@sematic_api.before_request
def log_request_start():
    logger().info(
        "Request start: %s",
        _request_string(flask.request),
    )


@sematic_api.after_request
def log_request_end(response):
    logger().info(
        "Request end: %s",
        _request_string(flask.request),
    )
    return response


def init_socketio():
    socketio = SocketIO(sematic_api, cors_allowed_origins="*")
    # This is necessary because starting version 5.7.0 python-socketio does not
    # accept connections to undeclared namespaces
    socketio.on_namespace(Namespace("/pipeline"))
    socketio.on_namespace(Namespace("/graph"))
    socketio.on_namespace(Namespace("/job"))
    return socketio


socketio = init_socketio()


def register_signal_handlers():
    def handler(signum, frame):
        logger = logging.getLogger()
        if signum == signal.SIGHUP:
            # Circle CI sends this between steps; and some environments may
            # send it for closed terminals. We don't want either to stop
            # the server.
            logger.warning(
                "Received SIGHUP. Ignoring. Please send SIGTERM to stop the process"
            )
            return

        # This is helpful so we know in the logs which signal caused
        # the process to stop.
        logger.warning("Received signal: %s. Quitting", signum)
        sys.exit(signum)

    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGABRT, handler)
    signal.signal(signal.SIGSEGV, handler)
    signal.signal(signal.SIGHUP, handler)


def run_socketio(debug=False):
    with open(get_config().server_pid_file_path, "w+") as fp:
        fp.write(str(os.getpid()))

    dictConfig(make_log_config(log_to_disk=True))
    register_signal_handlers()

    socketio.run(
        sematic_api,
        port=get_config().port,
        host=get_config().server_address,
        debug=debug,
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser("Sematic API server")
    parser.add_argument("--env", required=False, default="local", type=str)
    parser.add_argument("--debug", required=False, default=False, action="store_true")
    return parser.parse_args()


def run_wsgi(daemon: bool):
    options = {
        "bind": f"{get_config().server_address}:{get_config().port}",
        "workers": get_config().wsgi_workers_count,
        "worker_class": "geventwebsocket.gunicorn.workers.GeventWebSocketWorker",
        "daemon": daemon,
        "pidfile": get_config().server_pid_file_path,
        "logconfig_dict": make_log_config(log_to_disk=True),
        "certfile": os.environ.get("CERTIFICATE"),
        "keyfile": os.environ.get("PRIVATE_KEY"),
    }
    register_signal_handlers()
    SematicWSGI(sematic_api, options).run()


if __name__ == "__main__":
    args = parse_arguments()
    switch_env(args.env)

    if args.debug:
        run_socketio(args.debug)

    else:
        run_wsgi(False)
