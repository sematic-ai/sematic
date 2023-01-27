# Standard Library
from dataclasses import asdict
from http import HTTPStatus
from typing import Optional, Type, cast

# Third-party
import flask

# Sematic
from sematic.abstract_plugin import PluginScope
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate
from sematic.api.endpoints.request_parameters import jsonify_error
from sematic.config.settings import get_active_plugins
from sematic.db.models.user import User
from sematic.plugins.abstract_storage import AbstractStorage
from sematic.plugins.storage.local_storage import LocalStorage


@sematic_api.route("/api/v1/uploads/<namespace>/<key>/location", methods=["GET"])
@authenticate
def get_upload_location(
    user: Optional[User], namespace: str, key: str
) -> flask.Response:
    try:
        storage_plugin = get_active_plugins(
            PluginScope.STORAGE, default=[LocalStorage]
        )[0]
    except IndexError:
        return jsonify_error(
            "Incorrect storage plugin scope", HTTPStatus.INTERNAL_SERVER_ERROR
        )

    storage_class = cast(Type[AbstractStorage], storage_plugin)

    location = storage_class().get_write_location(namespace, key, user)

    return flask.jsonify(asdict(location))


@sematic_api.route("/api/v1/uploads/<namespace>/<key>/data", methods=["GET"])
@authenticate
def get_upload_data(user: Optional[User], namespace: str, key: str):
    try:
        storage_plugin = get_active_plugins(
            PluginScope.STORAGE, default=[LocalStorage]
        )[0]
    except IndexError:
        return jsonify_error(
            "Incorrect storage plugin scope", HTTPStatus.INTERNAL_SERVER_ERROR
        )

    storage_class = cast(Type[AbstractStorage], storage_plugin)

    location = storage_class().get_read_location(namespace, key, user)

    response = flask.redirect(location.location, code=HTTPStatus.FOUND)

    for key, value in location.headers.items():
        response.headers.set(key, value)

    return response
