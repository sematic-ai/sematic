# Standard Library
from typing import Optional

# Third-party
import flask

# Sematic
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate
from sematic.db.models.user import User
from sematic.db.queries import get_organizations


@sematic_api.route("/api/v1/organizations", methods=["GET"])
@authenticate
def list_organizations_endpoint(user: Optional[User]) -> flask.Response:
    """
    Retrieve the list of organizations.
    """
    # TODO: restrict to orgs that only the user has access to
    organizations = get_organizations()

    payload = [organization.to_json_encodable() for organization in organizations]

    return flask.jsonify(dict(content=payload))
