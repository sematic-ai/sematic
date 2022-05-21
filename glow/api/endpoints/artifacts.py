# Third-party
import flask

# Glow
from glow.api.app import glow_api
from glow.db.queries import get_run_input_artifacts


@glow_api.route("/api/v1/artifacts", methods=["GET"])
def list_artifacts_endpoint() -> flask.Response:
    args = flask.request.args
    consumer_run_id = args["consumer_run_ids"].split(",")[0]

    artifacts = get_run_input_artifacts(consumer_run_id)

    payload = {
        "content": [artifact.to_json_encodable() for artifact in artifacts.values()],
        "extra": {
            "run_mapping": {
                consumer_run_id: {
                    "input": {name: artifact.id for name, artifact in artifacts.items()}
                }
            }
        },
    }

    return flask.jsonify(payload)
