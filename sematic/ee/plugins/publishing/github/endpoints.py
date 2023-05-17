"""Metadata about the server itself."""

# Standard Library
from dataclasses import asdict
from logging import getLogger
from typing import Optional

# Third-party
import flask

# Sematic
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate
from sematic.db.models.user import User
from sematic.ee.plugins.publishing.github.check import check_commit

logger = getLogger(__name__)


@sematic_api.route("/api/v1/github/commit-check/<commit_sha>", methods=["GET"])
@authenticate
def run_commit_check(user: Optional[User], commit_sha: str) -> flask.Response:
    """Perform a check on the specified commit, update GitHub with the result and return.

    Returns
    -------
    A flask response with a json payload. The payload has 1 field, 'content'. The
    'content' field holds a commit check result with three fields: state, description,
    and target_url. These correspond to the fields described here:
    https://docs.github.com/en/rest/commits/statuses?apiVersion=2022-11-28#create-a-commit-status
    """
    payload = dict(
        content=asdict(check_commit(commit_sha)),
    )

    return flask.jsonify(payload)
