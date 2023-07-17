# Standard Library
from http import HTTPStatus
from typing import List, Optional

# Third-party
import flask

# Sematic
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate
from sematic.api.endpoints.request_parameters import (
    get_request_parameters,
    jsonify_error,
)
from sematic.db.db import db
from sematic.db.models.organization_user import OrganizationUser
from sematic.db.models.user import User


@sematic_api.route("/api/v1/organizations_users", methods=["GET"])
@authenticate
def list_organizations_users_endpoint(user: Optional[User]) -> flask.Response:
    """
    Retrieve information about users' membership in organizations.
    """
    try:
        parameters = get_request_parameters(
            args=flask.request.args, model=OrganizationUser
        )
        limit, order, sql_predicates = (
            parameters.limit,
            parameters.order,
            parameters.filters,
        )
    except ValueError as e:
        return jsonify_error(str(e), HTTPStatus.BAD_REQUEST)

    with db().get_session() as session:
        query = session.query(OrganizationUser)

        # TODO: restrict to orgs that only the user has access to
        if sql_predicates is not None:
            query = query.filter(sql_predicates)

        query = query.order_by(order(OrganizationUser.created_at))

        organizations_users: List[OrganizationUser] = query.limit(limit).all()

    payload = dict(
        content=[
            organization_user.to_json_encodable()
            for organization_user in organizations_users
        ]
    )

    return flask.jsonify(payload)
