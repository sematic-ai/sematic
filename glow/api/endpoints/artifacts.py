# Standard library
from collections import defaultdict
import typing

# Third-party
import flask

# Glow
from glow.api.app import glow_api
from glow.db.queries import get_runs_artifacts, get_runs_run_artifacts


@glow_api.route("/api/v1/artifacts", methods=["GET"])
def list_artifacts_endpoint() -> flask.Response:
    args = flask.request.args
    run_ids = args["run_ids"].split(",")

    artifacts = get_runs_artifacts(run_ids)
    run_artifacts = get_runs_run_artifacts(run_ids)

    run_mapping: typing.Dict[
        str, typing.Dict[str, typing.Dict[typing.Optional[str], str]]
    ] = defaultdict(lambda: dict(input={}, output={}))

    for run_artifact in run_artifacts:
        relationship = typing.cast(str, run_artifact.relationship)
        run_mapping[run_artifact.run_id][relationship.lower()][
            run_artifact.name
        ] = run_artifact.artifact_id

    payload = {
        "content": [artifact.to_json_encodable() for artifact in artifacts],
        "extra": {"run_mapping": run_mapping},
    }

    return flask.jsonify(payload)
