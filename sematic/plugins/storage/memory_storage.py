# Standard Library
from typing import Any, Dict, Optional

# Third-party
import flask

# Sematic
from sematic.abstract_plugin import AbstractPlugin, PluginVersion
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate
from sematic.db.models.user import User
from sematic.plugins.abstract_storage import (
    AbstractStorage,
    NoSuchStorageKeyError,
    PayloadType,
    ReadPayload,
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
        return "github.com/sematic-ai"

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

    def get_write_location(self, namespace: str, key: str) -> str:
        return f"/memory_upload/{namespace}/{key}"

    def get_read_payload(self, namespace: str, key: str) -> ReadPayload:
        try:
            content = self._store[self.get_write_location(namespace, key)]
        except KeyError:
            raise NoSuchStorageKeyError(self.__class__, key)

        return ReadPayload(type_=PayloadType.BYTES, content=content)


# This endpoint should only be registered for test purposes
@sematic_api.route("/api/v1/memory_upload/<namespace>/<key>", methods=["PUT"])
@authenticate
def memory_upload_endpoint(
    user: Optional[User], namespace: str, key: str
) -> flask.Response:
    payload = flask.request.data

    MemoryStorage.set(MemoryStorage().get_write_location(namespace, key), payload)

    return flask.jsonify({})
