# Standard Library
import logging
from http import HTTPStatus
from typing import List, Optional, Type, cast

# Third-party
import flask
from sqlalchemy.orm.exc import NoResultFound

# Sematic
from sematic.abstract_plugin import PluginScope
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate
from sematic.api.endpoints.request_parameters import (
    get_request_parameters,
    jsonify_error,
)
from sematic.config.settings import get_active_plugins
from sematic.db.db import db
from sematic.db.models.artifact import Artifact
from sematic.db.models.user import User
from sematic.db.queries import get_artifact
from sematic.plugins.abstract_storage import AbstractStorage, PayloadType
from sematic.plugins.storage.local_storage import LocalStorage

logger = logging.getLogger(__name__)


@sematic_api.route("/api/v1/artifacts", methods=["GET"])
@authenticate
def list_artifacts_endpoint(user: Optional[User] = None) -> flask.Response:
    limit, order, _, _, sql_predicates = get_request_parameters(
        args=flask.request.args, model=Artifact
    )

    with db().get_session() as session:
        query = session.query(Artifact)

        if sql_predicates is not None:
            query = query.filter(sql_predicates)

        query = query.order_by(order(Artifact.created_at))

        artifacts: List[Artifact] = query.limit(limit).all()

    payload = dict(content=[artifacts.to_json_encodable() for artifacts in artifacts])

    return flask.jsonify(payload)


@sematic_api.route("/api/v1/artifacts/<artifact_id>", methods=["GET"])
@authenticate
def get_artifact_endpoint(user: Optional[User], artifact_id: str) -> flask.Response:
    """
    Retrieve an artifact by its ID.

    Parameters
    ----------
    artifact_id: str
        ID of artifact to retrieve

    Response
    --------
    content: Artifact
        The requested artifact in JSON format
    """
    try:
        artifact = get_artifact(artifact_id)
    except NoResultFound:
        return jsonify_error(
            "No Artifact with id {}".format(repr(artifact_id)), HTTPStatus.NOT_FOUND
        )

    payload = dict(content=artifact.to_json_encodable())

    return flask.jsonify(payload)


@sematic_api.route("/api/v1/artifacts/<artifact_id>/location", methods=["GET"])
@authenticate
def get_artifact_location_endpoint(user: Optional[User], artifact_id: str):
    # TODO: Validate that user has permission to access artifact
    try:
        storage_class = _get_storage_plugin()
    except NoActivePluginError:
        return jsonify_error(
            "Incorrect storage plugin scope", HTTPStatus.INTERNAL_SERVER_ERROR
        )

    logger.info("Using storage plug-in %s", storage_class)

    location = storage_class().get_write_location("artifacts", artifact_id)

    return flask.jsonify(dict(location=location))


@sematic_api.route("/api/v1/artifacts/<artifact_id>/data", methods=["GET"])
@authenticate
def get_artifact_data_endpoint(user: Optional[User], artifact_id: str):
    # TODO: Validate that user has permission to access artifact
    try:
        storage_class = _get_storage_plugin()
    except NoActivePluginError:
        return jsonify_error(
            "Incorrect storage plugin scope", HTTPStatus.INTERNAL_SERVER_ERROR
        )

    logger.info("Using storage plug-in %s", storage_class)

    read_payload = storage_class().get_read_payload("artifacts", artifact_id)

    if read_payload.type_ is PayloadType.URL:
        return flask.redirect(read_payload.content, code=HTTPStatus.FOUND)

    return flask.Response(read_payload.content)


class NoActivePluginError(Exception):
    pass


def _get_storage_plugin() -> Type[AbstractStorage]:
    try:
        storage_plugin = get_active_plugins(
            PluginScope.STORAGE, default=[LocalStorage]
        )[0]
    except IndexError:
        raise NoActivePluginError()

    storage_class = cast(Type[AbstractStorage], storage_plugin)

    return storage_class
