# Standard Library
import logging
import urllib.parse
from http import HTTPStatus
from typing import Optional

# Third-party
import flask

# Sematic
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate
from sematic.api.endpoints.request_parameters import jsonify_error
from sematic.db.models.user import User
from sematic.plugins.abstract_storage import get_storage_plugins
from sematic.plugins.storage.local_storage import LocalStorage

logger = logging.getLogger(__name__)


# Other endpoints under the /api/v1/storage path may be added by individual
# storage plugins (e.g. /api/v1/storage/<namespace>/<key>/memory by memory_storage)


@sematic_api.route("/api/v1/storage/<namespace>/<key>/location", methods=["GET"])
@authenticate
def get_storage_location(
    user: Optional[User], namespace: str, key: str
) -> flask.Response:
    """
    Get the URL to which to PUT the payload to store.

    Response
    --------
    url: str
        URL to PUT to to store a binary payload.
    request_headers: Dict[str, str]
        Headers to set on the PUT request.
    """
    namespace = urllib.parse.unquote(namespace)
    key = urllib.parse.unquote(key)

    try:
        storage_plugin = get_storage_plugins([LocalStorage])[0]
    except Exception as e:
        logger.error(e)

        return jsonify_error(
            "Incorrect storage plugin scope", HTTPStatus.INTERNAL_SERVER_ERROR
        )

    destination = storage_plugin().get_write_destination(namespace, key, user)

    return flask.jsonify(
        dict(
            url=destination.url,
            request_headers=destination.request_headers,
        )
    )


@sematic_api.route("/api/v1/storage/<namespace>/<key>/data", methods=["GET"])
@authenticate
def get_storage_data_endpoint(user: Optional[User], namespace: str, key: str):
    """
    Redirect to the location of the stored payload.

    Response
    --------
    A redirection to the actual binary payload.
    """
    return get_stored_data_redirect(user, namespace, key)


def get_stored_data_redirect(user: Optional[User], namespace: str, key: str):
    try:
        storage_plugin = get_storage_plugins([LocalStorage])[0]
    except Exception as e:
        logger.error(e)

        return jsonify_error(
            "Incorrect storage plugin scope", HTTPStatus.INTERNAL_SERVER_ERROR
        )

    destination = storage_plugin().get_read_destination(namespace, key, user)

    response = flask.redirect(destination.url, code=HTTPStatus.FOUND)

    for key, value in destination.request_headers.items():
        response.headers.set(key, value)

    return response
