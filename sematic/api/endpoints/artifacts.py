# Standard Library
from http import HTTPStatus
from typing import List, Optional

# Third-party
import flask
import sqlalchemy
from sqlalchemy.orm.exc import NoResultFound

# Sematic
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate
from sematic.api.endpoints.request_parameters import (
    get_request_parameters,
    jsonify_error,
)
from sematic.db.db import db
from sematic.db.models.artifact import Artifact
from sematic.db.models.user import User
from sematic.db.queries import get_artifact


@sematic_api.route("/api/v1/artifacts", methods=["GET"])
@authenticate
def list_artifacts_endpoint(user: Optional[User] = None) -> flask.Response:
    limit, _, _, sql_predicates = get_request_parameters(flask.request.args, Artifact)

    with db().get_session() as session:
        query = session.query(Artifact)

        if sql_predicates is not None:
            query = query.filter(sql_predicates)

        query = query.order_by(sqlalchemy.desc(Artifact.created_at))

        artifacts: List[Artifact] = query.limit(limit).all()

    payload = dict(content=[artifacts.to_json_encodable() for artifacts in artifacts])

    return flask.jsonify(payload)


@sematic_api.route("/api/v1/artifacts/<artifact_id>", methods=["GET"])
@authenticate
def get_artifact_endpoint(user: Optional[User], artifact_id: str) -> flask.Response:
    """
    Retrive an artifact.

    Parameters
    ----------
    artifact_id: str
        ID of artifact to retrieve

    Returns
    -------
    content: Artifact
        The requested artifact in JSON format
    """
    try:
        artifact = get_artifact(artifact_id)
    except NoResultFound:
        return jsonify_error(
            "No Artifact with id {}".format(repr(artifact_id)), HTTPStatus.NOT_FOUND
        )

    payload = dict(
        content=artifact.to_json_encodable(),
    )

    return flask.jsonify(payload)
