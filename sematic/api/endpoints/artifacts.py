# Standard library
from typing import List

# Third-party
import flask
import sqlalchemy

# Sematic
from sematic.api.app import sematic_api
from sematic.api.endpoints.request_parameters import get_request_parameters
from sematic.db.models.artifact import Artifact
from sematic.db.db import db


@sematic_api.route("/api/v1/artifacts", methods=["GET"])
def list_artifacts_endpoint() -> flask.Response:
    limit, _, _, sql_predicates = get_request_parameters(flask.request.args, Artifact)

    with db().get_session() as session:
        query = session.query(Artifact)

        if sql_predicates is not None:
            query = query.filter(sql_predicates)

        query = query.order_by(sqlalchemy.desc(Artifact.created_at))

        artifacts: List[Artifact] = query.limit(limit).all()

    payload = dict(content=[artifacts.to_json_encodable() for artifacts in artifacts])

    return flask.jsonify(payload)
