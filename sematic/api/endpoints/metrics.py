# Standard Library
from http import HTTPStatus
from typing import Any, Dict, Optional

# Third-party
import flask

# Sematic
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate
from sematic.api.endpoints.events import (
    broadcast_pipeline_metrics_update,
    broadcast_run_metrics_update,
)
from sematic.api.endpoints.payloads import get_compact_metrics_payload
from sematic.api.endpoints.request_parameters import jsonify_error
from sematic.db.models.metric import Metric, MetricScope
from sematic.db.models.user import User
from sematic.db.queries import (
    clear_run_metrics,
    get_pipeline_metrics,
    get_run,
    get_run_metrics,
    save_metric,
)


@sematic_api.route("/api/v1/metrics", methods=["POST"])
@authenticate
def post_metric(user: Optional[User]) -> flask.Response:
    payload: Dict[str, Any] = flask.request.json  # type: ignore
    if "metric" not in payload:
        return jsonify_error(
            "Payload is missing a 'metric' key", HTTPStatus.BAD_REQUEST
        )

    metric = Metric.from_json_encodable(payload["metric"])

    metric = save_metric(metric)

    if metric.scope is MetricScope.PIPELINE:
        root_run = get_run(metric.root_id)
        broadcast_pipeline_metrics_update(root_run.calculator_path, user)

    if metric.scope is MetricScope.RUN:
        broadcast_run_metrics_update(metric.run_id, user)

    return flask.jsonify({})


@sematic_api.route("/api/v1/metrics", methods=["GET"])
@authenticate
def list_metrics(user: Optional[User]) -> flask.Response:
    args = flask.request.args

    if "calculator_path" in args:
        metrics = get_pipeline_metrics(args["calculator_path"])
    elif "run_id" in args:
        metrics = get_run_metrics(args["run_id"])
    else:
        return jsonify_error(
            "No calculator_path or run_id was passed", HTTPStatus.BAD_REQUEST
        )

    if args.get("format", None) == "compact":
        return flask.jsonify(dict(content=get_compact_metrics_payload(metrics)))
    else:
        return flask.jsonify(dict(content=list(map(Metric.to_json_encodable, metrics))))


@sematic_api.route("/api/v1/metrics/<run_id>", methods=["DELETE"])
@authenticate
def clear_metrics(user: Optional[User], run_id: str) -> flask.Response:
    clear_run_metrics(run_id)
    return flask.jsonify({})
