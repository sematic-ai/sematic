# Standard Library
from typing import Optional

# Third-party
import flask

# Sematic
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate
from sematic.db.models.user import User
from sematic.db.queries import get_users


@sematic_api.route("/api/v1/users", methods=["GET"])
@authenticate
def list_users_endpoint(user: Optional[User]) -> flask.Response:
    """
    Retrieve list of users.
    """
    users = get_users()

    payload = [user.to_json_encodable(redact=True) for user in users]

    return flask.jsonify(dict(content=payload))
