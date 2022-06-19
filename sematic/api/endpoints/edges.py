# Standard Library
from typing import List

# Third-party
import sqlalchemy
import flask

# Sematic
from sematic.api.app import sematic_api
from sematic.api.endpoints.request_parameters import get_request_parameters
from sematic.db.db import db
from sematic.db.models.edge import Edge


@sematic_api.route("/api/v1/edges", methods=["GET"])
def list_edges_endpoint() -> flask.Response:
    limit, _, _, sql_predicates = get_request_parameters(flask.request.args, Edge)

    with db().get_session() as session:
        query = session.query(Edge)

        if sql_predicates is not None:
            query = query.filter(sql_predicates)

        query = query.order_by(sqlalchemy.desc(Edge.created_at))

        edges: List[Edge] = query.limit(limit).all()

    payload = dict(content=[edge.to_json_encodable() for edge in edges])

    return flask.jsonify(payload)
