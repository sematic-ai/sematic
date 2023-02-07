# Standard Library
import logging
from http import HTTPStatus
from typing import List, Optional

# Third-party
import flask
from sqlalchemy.orm.exc import NoResultFound

# Sematic
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate
from sematic.api.endpoints.request_parameters import (
    get_request_parameters,
    jsonify_error,
)
from sematic.api.endpoints.storage import get_storage_plugin, get_stored_data_redirect
from sematic.db.db import db
from sematic.db.models.artifact import Artifact
from sematic.db.models.user import User
from sematic.db.queries import get_artifact

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


# Kept for backward compatibility with 0.23.0
@sematic_api.route("/api/v1/artifacts/<artifact_id>/location", methods=["GET"])
@authenticate
def get_artifact_location_endpoint(user: Optional[User], artifact_id: str):
    try:
        storage_plugin = get_storage_plugin()
    except Exception as e:
        logger.exception("Unable to load the storage plugin: %s", str(e))

        return jsonify_error(
            "Incorrect storage plugin scope", HTTPStatus.INTERNAL_SERVER_ERROR
        )

    destination = storage_plugin().get_write_destination("artifacts", artifact_id, user)

    location = destination.url

    # If this is a Sematic URL, older clients expect the relative path and will add
    # auth headers on their own
    url_parts = location.split("/api/v1")
    if len(url_parts) > 1:
        location = url_parts[1]

    return flask.jsonify(dict(location=location))


# Kept for backward compatibility with 0.23.0
@sematic_api.route("/api/v1/artifacts/<artifact_id>/data", methods=["GET"])
@authenticate
def get_artifact_data_endpoint(user: Optional[User], artifact_id: str):
    return get_stored_data_redirect(user, "artifacts", artifact_id)
