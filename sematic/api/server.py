# Standard Library
import argparse
import logging
import os
import signal
import sys
from logging.config import dictConfig

# Third-party
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
import sematic.api.endpoints.metrics  # noqa: F401
import sematic.api.endpoints.notes  # noqa: F401
import sematic.api.endpoints.resolutions  # noqa: F401
import sematic.api.endpoints.runs  # noqa: F401
import sematic.api.endpoints.storage  # noqa: F401
from sematic.api.app import sematic_api
from sematic.api.wsgi import SematicWSGI
from sematic.config.config import get_config, switch_env  # noqa: F401
from sematic.config.settings import import_plugins

# Some plugins may register endpoints
import_plugins()


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


def init_socketio():
    socketio = SocketIO(sematic_api, cors_allowed_origins="*")
    # This is necessary because starting version 5.7.0 python-socketio does not
    # accept connections to undeclared namespaces
    socketio.on_namespace(Namespace("/pipeline"))
    socketio.on_namespace(Namespace("/graph"))
    socketio.on_namespace(Namespace("/metrics"))
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

    dictConfig(make_log_config())
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
        "logconfig_dict": make_log_config(),
        "certfile": os.environ.get("CERTIFICATE"),
        "keyfile": os.environ.get("PRIVATE_KEY"),
    }
    register_signal_handlers()
    SematicWSGI(sematic_api, options).run()


def make_log_config():
    stdout_handler_list = ["stdout"] if get_config().server_log_to_stdout else []
    full_handler_list = ["default", "error"] + stdout_handler_list
    root_logger_config = {"level": "INFO", "handlers": full_handler_list}
    log_rotation_settings = {
        "formatter": "standard",
        "class": "logging.handlers.RotatingFileHandler",
        "maxBytes": 500 * 2**20,  # 500 MB
        "backupCount": 20,
    }
    config = {
        "version": 1,
        "root": root_logger_config,
        "disable_existing_loggers": True,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            },
        },
        "handlers": {
            "default": dict(
                level="INFO",
                filename=os.path.join(get_config().config_dir, "access.log"),
                **log_rotation_settings,
            ),
            "error": dict(
                level="ERROR",
                filename=os.path.join(get_config().config_dir, "error.log"),
                **log_rotation_settings,
            ),
            "stdout": {
                "formatter": "standard",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "sematic": root_logger_config,
            "gunicorn.error": {"level": "ERROR", "handlers": full_handler_list},
            "gunicorn.access": {"level": "INFO", "handlers": full_handler_list},
        },
    }
    return config


if __name__ == "__main__":
    args = parse_arguments()
    switch_env(args.env)

    if args.debug:
        run_socketio(args.debug)

    else:
        run_wsgi(False)
