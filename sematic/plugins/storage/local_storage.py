# Standard Library
import logging
import os
from http import HTTPStatus
from typing import Dict, Iterable, List, Optional, Type

# Third-party
import flask

# Sematic
from sematic.abstract_plugin import (
    SEMATIC_PLUGIN_AUTHOR,
    AbstractPlugin,
    AbstractPluginSettingsVar,
    PluginVersion,
)
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import API_KEY_HEADER, authenticate
from sematic.api.endpoints.request_parameters import jsonify_error
from sematic.config.config import get_config
from sematic.config.settings import get_plugin_setting
from sematic.db.models.user import User
from sematic.plugins.abstract_storage import AbstractStorage, StorageDestination

logger = logging.getLogger(__name__)

_PLUGIN_VERSION = (0, 1, 0)


class LocalStorageSettingsVar(AbstractPluginSettingsVar):
    LOCAL_STORAGE_PATH = "LOCAL_STORAGE_PATH"


class LocalStorage(AbstractStorage, AbstractPlugin):
    """
    A local storage implementation of the `AbstractStorage` interface. Values
    are stores in the data directory of the Sematic directory, typically at
    `~/.sematic/data`.
    """

    @staticmethod
    def get_author() -> str:
        return SEMATIC_PLUGIN_AUTHOR

    @staticmethod
    def get_version() -> PluginVersion:
        return _PLUGIN_VERSION

    @classmethod
    def get_settings_vars(cls) -> Type[AbstractPluginSettingsVar]:
        return LocalStorageSettingsVar

    def get_write_destination(
        self, namespace: str, key: str, user: Optional[User]
    ) -> StorageDestination:
        return StorageDestination(
            uri=f"sematic:///api/v1/storage/{namespace}/{key}/local",
            request_headers=_make_headers(user),
        )

    def get_read_destination(
        self, namespace: str, key: str, user: Optional[User]
    ) -> StorageDestination:
        return StorageDestination(
            uri=f"sematic:///api/v1/storage/{namespace}/{key}/local",
            request_headers=_make_headers(user),
        )

    def get_child_paths(self, key_prefix: str) -> List[str]:
        return [
            os.path.join(dp, f)
            for dp, _, fn in os.walk(os.path.join(_get_data_dir(), key_prefix))
            for f in fn
        ]

    def get_line_stream(self, key: str, encoding: str = "utf8") -> Iterable[str]:
        with open(os.path.join(_get_data_dir(), key), "rb") as f:
            for line in f:
                yield str(line, encoding=encoding)


def _make_headers(user: Optional[User]) -> Dict[str, str]:
    headers = {"Content-Type": "application/octet-stream"}

    if user is not None:
        headers[API_KEY_HEADER] = user.api_key

    return headers


@sematic_api.route("/api/v1/storage/<namespace>/<key>/local", methods=["PUT"])
@authenticate
def upload_endpoint(user: Optional[User], namespace: str, key: str) -> flask.Response:
    # TODO: Validate that user has permissions to upload.
    # TODO: Breakdown into two different endpoints for artifacts and futures
    payload = flask.request.data

    os.makedirs(os.path.join(_get_data_dir(), namespace), exist_ok=True)

    with open(os.path.join(_get_data_dir(), namespace, key), "wb") as file:
        file.write(payload)

    return flask.jsonify({})


@sematic_api.route("/api/v1/storage/<namespace>/<key>/local", methods=["GET"])
@authenticate
def download_endpoint(user: Optional[User], namespace: str, key: str) -> flask.Response:
    try:
        with open(os.path.join(_get_data_dir(), namespace, key), "rb") as file:
            content = file.read()
    except FileNotFoundError:
        return jsonify_error(
            error="No such namespace or key: {namespace} {key}",
            status=HTTPStatus.NOT_FOUND,
        )

    response = flask.Response(content)
    response.headers.set("Cache-Control", "max-age=31536000, immutable, private")

    return response


# For easier mocking
def _get_data_dir() -> str:
    return get_plugin_setting(
        LocalStorage, LocalStorageSettingsVar.LOCAL_STORAGE_PATH, get_config().data_dir
    )
