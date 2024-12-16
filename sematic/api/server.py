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
import socketio  # type: ignore
import uvicorn  # type: ignore
from asgiref.wsgi import WsgiToAsgi  # type: ignore
from flask import jsonify, send_file
from socketio import ASGIApp, AsyncNamespace, AsyncServer, Namespace  # type: ignore
from werkzeug.exceptions import HTTPException, InternalServerError

# Sematic
import sematic.api.endpoints.artifacts  # noqa: F401
import sematic.api.endpoints.auth  # noqa: F401
import sematic.api.endpoints.edges  # noqa: F401
import sematic.api.endpoints.events  # noqa: F401
import sematic.api.endpoints.external_resources  # noqa: F401
import sematic.api.endpoints.meta  # noqa: F401
import sematic.api.endpoints.notes  # noqa: F401
import sematic.api.endpoints.organizations  # noqa: F401
import sematic.api.endpoints.organizations_users  # noqa: F401
import sematic.api.endpoints.resolutions  # noqa: F401
import sematic.api.endpoints.runs  # noqa: F401
import sematic.api.endpoints.storage  # noqa: F401
import sematic.api.endpoints.users  # noqa: F401
from sematic.api.app import sematic_api

# Endpoint modules need to be imported for endpoints
# to be registered.
from sematic.api.endpoints.events import register_sio_server, starlette_app
from sematic.config.config import get_config, switch_env  # noqa: F401
from sematic.config.settings import import_plugins
from sematic.logs import make_log_config
from sematic.utils.daemonize import daemonize


#


SOCKET_IO_NAMESPACES = [
    "/pipeline",
    "/graph",
    "/job",
    "/metrics",
]


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


def _request_string(request, response_code: Optional[int] = None) -> str:
    """Get a string representing the request for use in logs."""
    query_string = (
        f"?{str(request.query_string, encoding='utf8')}"
        if len(request.query_string) > 0
        else ""
    )
    response_code_section = f" {response_code}" if response_code is not None else ""
    request_string = (
        f"{request.remote_addr} {request.user_agent} "
        f"{request.method} {request.path}{query_string}{response_code_section}"
    )
    return request_string


@sematic_api.before_request
def log_request_start():
    """Log that the request is starting."""
    logger().info(
        "Request start: %s",
        _request_string(flask.request),
    )


@sematic_api.errorhandler(Exception)
def handle_exception(e):
    # Ensure we've logged uncaught exceptions
    logger().exception(e)

    # pass through HTTP errors, they are already valid responses for flask.
    if isinstance(e, HTTPException):
        return e

    # convert other remaining to generic 500s.
    return InternalServerError(description="Unknown error", original_exception=e)


@sematic_api.after_request
def log_request_end(response):
    """Log that the request is ending."""
    logger().info(
        "Request end: %s",
        _request_string(flask.request, response.status_code),
    )
    return response


def register_signal_handlers():
    """Register handlers to log messages and exit the server for appropriate signals."""

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


def init_socket_io_server(make_async):
    """Declare namespaces for SocketIO and init the SocketIO WSGI/ASGI app."""
    server_class = AsyncServer if make_async else socketio.Server
    async_mode = "asgi" if make_async else "threading"
    namespace_class = AsyncNamespace if make_async else Namespace

    sio = server_class(async_mode=async_mode, cors_allowed_origins="*")
    for namespace in SOCKET_IO_NAMESPACES:
        sio.register_namespace(namespace_class(namespace))
    register_sio_server(sio)
    return sio


def run_locally(debug=False, make_daemon=False):
    """Run the server for local (non-production) usage."""
    dictConfig(make_log_config(log_to_disk=True, level=logging.INFO))
    register_signal_handlers()

    sio = init_socket_io_server(make_async=False)
    sematic_api.wsgi_app = socketio.WSGIApp(sio, sematic_api.wsgi_app)
    if make_daemon:
        daemonize(False)

    with open(get_config().server_pid_file_path, "w+") as fp:
        fp.write(str(os.getpid()))

    uvicorn.run(
        sematic_api,
        host=get_config().server_address,
        port=get_config().port,
        log_config=make_log_config(log_to_disk=True),
        interface="wsgi",
        workers=None,
    )


def parse_arguments() -> argparse.Namespace:
    """Parse the command line arguments."""
    parser = argparse.ArgumentParser("Sematic API server")
    parser.add_argument("--env", required=False, default="local", type=str)
    parser.add_argument("--debug", required=False, default=False, action="store_true")
    return parser.parse_args()


def app():
    """Callable to produce a WSGI/ASGI app for a WSGI/ASGI server."""
    dictConfig(make_log_config(log_to_disk=True, level=logging.INFO))
    register_signal_handlers()

    if os.environ.get("SEMATIC_SOCKET_IO_ONLY", "") != "":
        sio = init_socket_io_server(make_async=True)
        full_app = ASGIApp(sio, starlette_app)
    else:
        full_app = WsgiToAsgi(sematic_api)

    return full_app


if __name__ == "__main__":
    args = parse_arguments()
    switch_env(args.env)

    if args.debug:
        run_locally(args.debug, make_daemon=False)

    else:
        # Using uvicorn.run with more than one worker appears to crash it, but
        # using more than one worker when invoking `uvicorn` on the command line
        # works.
        print(
            "To run the server in production, please launch it using uvicorn directly. "
            "For an example call, refer to "
            "https://github.com/sematic-ai/sematic/blob/main/docker/Dockerfile.server"
        )
        sys.exit(1)
