# Third-party
import flask

# Glow
from glow.api.app import glow_api
from glow.db.queries import list_runs


@glow_api.route("/api/v1/runs", methods=["GET"])
def list_runs_endpoint() -> flask.Response:
    runs = list_runs()

    return flask.jsonify({"runs": [run.to_json_encodable() for run in runs]})
