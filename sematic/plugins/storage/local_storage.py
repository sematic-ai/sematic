# Standard Library
import logging
import os
from typing import Dict, Optional

# Third-party
import flask

# Sematic
from sematic.abstract_plugin import AbstractPlugin, PluginVersion
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import API_KEY_HEADER, authenticate
from sematic.config.config import get_config
from sematic.config.server_settings import get_api_address
from sematic.db.models.user import User
from sematic.plugins.abstract_storage import (
    AbstractStorage,
    Location,
    NoSuchStorageKeyError,
)

logger = logging.getLogger(__name__)

_PLUGIN_VERSION = (0, 1, 0)


class LocalStorage(AbstractStorage, AbstractPlugin):
    """
    A local storage implementation of the `AbstractStorage` interface. Values
    are stores in the data directory of the Sematic directory, typically at
    `~/.sematic/data`.
    """

    @staticmethod
    def get_author() -> str:
        return "github.com/sematic-ai"

    @staticmethod
    def get_version() -> PluginVersion:
        return _PLUGIN_VERSION

    def get_write_location(
        self, namespace: str, key: str, user: Optional[User]
    ) -> Location:

        return Location(
            location=f"{get_api_address()}/api/v1/uploads/{namespace}/{key}/local",
            headers=_make_headers(user),
        )

    def get_read_location(
        self, namespace: str, key: str, user: Optional[User]
    ) -> Location:
        return Location(
            location=f"{get_api_address()}/api/v1/uploads/{namespace}/{key}/local",
            headers=_make_headers(user),
        )


def _make_headers(user: Optional[User]) -> Dict[str, str]:
    headers = {"Content-Type": "application/octet-stream"}

    if user is not None:
        headers[API_KEY_HEADER] = user.api_key

    return headers


@sematic_api.route("/api/v1/uploads/<namespace>/<key>/local", methods=["PUT"])
@authenticate
def upload_endpoint(user: Optional[User], namespace: str, key: str) -> flask.Response:
    # TODO: Validate that user has permissions to upload.
    # TODO: Breakdown into two different endpoints for artifacts and futures
    payload = flask.request.data

    os.makedirs(os.path.join(_get_data_dir(), namespace), exist_ok=True)

    with open(os.path.join(_get_data_dir(), namespace, key), "wb") as file:
        file.write(payload)

    return flask.jsonify({})


@sematic_api.route("/api/v1/uploads/<namespace>/<key>/local", methods=["GET"])
@authenticate
def download_endpoint(user: Optional[User], namespace: str, key: str) -> flask.Response:
    try:
        with open(os.path.join(_get_data_dir(), namespace, key), "rb") as file:
            content = file.read()
    except FileNotFoundError:
        raise NoSuchStorageKeyError(LocalStorage, key)

    return flask.Response(content)


# For easier mocking
def _get_data_dir() -> str:
    return get_config().data_dir
