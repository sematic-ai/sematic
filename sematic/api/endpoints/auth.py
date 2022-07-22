# Standard library
from http import HTTPStatus

# Third-party
import flask
from google.oauth2 import id_token  # type: ignore
from google.auth.transport import requests  # type: ignore

# Sematic
from sematic.api.app import sematic_api
from sematic.api.endpoints.request_parameters import (
    jsonify_error,
)


@sematic_api.route("/login", methods=["POST"])
def login() -> flask.Response:
    if not flask.request or not flask.request.json or "token" not in flask.request.json:
        return jsonify_error("Please provide a login token", HTTPStatus.BAD_REQUEST)

    token = flask.request.json["token"]

    idinfo = id_token.verify_oauth2_token(
        token,
        requests.Request(),
        "977722105393-257kdkrc5dfbpu0jcsd8etn1k4u4q4ut.apps.googleusercontent.com",
    )

    print(idinfo)

    return flask.jsonify({})
