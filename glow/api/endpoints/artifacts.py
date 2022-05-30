# Standard library
from typing import Dict, List

# Third-party
import flask
import sqlalchemy

# Glow
from glow.api.app import glow_api
from glow.api.endpoints.request_parameters import get_request_parameters
from glow.db.models.artifact import Artifact
from glow.db.db import db


_COLUMN_MAPPING: Dict[str, sqlalchemy.Column] = {
    column.name: column for column in Artifact.__table__.columns
}


@glow_api.route("/api/v1/artifacts", methods=["GET"])
def list_artifacts_endpoint() -> flask.Response:
    limit, _, _, sql_predicates = get_request_parameters(
        flask.request.args, _COLUMN_MAPPING
    )

    with db().get_session() as session:
        query = session.query(Artifact)

        if sql_predicates is not None:
            query = query.filter(sql_predicates)

        query = query.order_by(sqlalchemy.desc(Artifact.created_at))

        artifacts: List[Artifact] = query.limit(limit).all()

    payload = dict(content=[artifacts.to_json_encodable() for artifacts in artifacts])

    return flask.jsonify(payload)
