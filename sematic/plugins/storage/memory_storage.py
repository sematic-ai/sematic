# Standard Library
from http import HTTPStatus
from typing import Any, Dict, Iterable, List, Optional

# Third-party
import flask

# Sematic
from sematic.abstract_plugin import SEMATIC_PLUGIN_AUTHOR, AbstractPlugin, PluginVersion
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import API_KEY_HEADER, authenticate
from sematic.api.endpoints.request_parameters import jsonify_error
from sematic.db.models.user import User
from sematic.plugins.abstract_storage import (
    AbstractStorage,
    NoSuchStorageKeyError,
    StorageDestination,
)


_PLUGIN_VERSION = (0, 1, 0)


class MemoryStorage(AbstractStorage, AbstractPlugin):
    """
    An in-memory key/value store implementing the `AbstractStorage` interface.

    This is only usable if both resolver and server are in the same Python
    process, i.e. only in a unit test.
    """

    @staticmethod
    def get_author() -> str:
        return SEMATIC_PLUGIN_AUTHOR

    @staticmethod
    def get_version() -> PluginVersion:
        return _PLUGIN_VERSION

    _store: Dict[str, Any] = {}

    @classmethod
    def get(cls, key: str):
        try:
            return cls._store[key]
        except KeyError:
            raise NoSuchStorageKeyError(cls, key)

    @classmethod
    def set(cls, key: str, value: bytes):
        cls._store[key] = value

    def get_write_destination(
        self, namespace: str, key: str, user: Optional[User]
    ) -> StorageDestination:
        return StorageDestination(
            uri=f"sematic:///api/v1/storage/{namespace}/{key}/memory",
            request_headers=_make_headers(user),
        )

    def get_read_destination(
        self, namespace: str, key: str, user: Optional[User]
    ) -> StorageDestination:
        return StorageDestination(
            uri=f"sematic:///api/v1/storage/{namespace}/{key}/memory",
            request_headers=_make_headers(user),
        )

    def get_child_paths(self, key_prefix: str) -> List[str]:
        return [key for key in self._store if key.startswith(key_prefix)]

    def get_line_stream(self, key: str, encoding: str = "utf8") -> Iterable[str]:
        content = str(self.get(key), encoding=encoding)

        for line in content.split("\n"):
            yield line


def _make_headers(user: Optional[User]) -> Dict[str, str]:
    headers = {"Content-Type": "application/octet-stream"}

    if user is not None:
        headers[API_KEY_HEADER] = user.api_key

    return headers


# These endpoints should only be registered for test purposes


@sematic_api.route("/api/v1/storage/<namespace>/<key>/memory", methods=["GET"])
@authenticate
def memory_download_endpoint(
    user: Optional[User], namespace: str, key: str
) -> flask.Response:
    try:
        content = MemoryStorage.get(f"{namespace}/{key}")
    except NoSuchStorageKeyError:
        return jsonify_error(
            f"No such namespace or key: {namespace}/{key}", HTTPStatus.NOT_FOUND
        )

    return flask.Response(content)


@sematic_api.route("/api/v1/storage/<namespace>/<key>/memory", methods=["PUT"])
@authenticate
def memory_upload_endpoint(
    user: Optional[User], namespace: str, key: str
) -> flask.Response:
    payload = flask.request.data

    MemoryStorage.set(f"{namespace}/{key}", payload)

    return flask.jsonify({})
