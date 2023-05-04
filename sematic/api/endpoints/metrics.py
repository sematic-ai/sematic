# Standard Library
import datetime
import enum
import json
import logging
import time
from http import HTTPStatus
from typing import Any, Dict, List, Literal, Optional, Type, cast

# Third-party
import flask

# Sematic
from sematic.abstract_system_metric import AbstractSystemMetric
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate

# from sematic.api.endpoints.events import broadcast_metrics_update
from sematic.api.endpoints.request_parameters import jsonify_error
from sematic.db.models.run import Run
from sematic.db.models.user import User
from sematic.metrics.func_effective_runtime_metric import FuncEffectiveRuntimeMetric
from sematic.metrics.func_success_rate_metric import FuncSuccessRateMetric
from sematic.metrics.metric_point import MetricPoint
from sematic.metrics.run_count_metric import RunCountMetric
from sematic.plugins.abstract_metrics_storage import (
    GroupBy,
    MetricsFilter,
    NoMetricError,
    RollUp,
    get_metrics_storage_plugins,
)
from sematic.plugins.metrics_storage.sql.sql_metrics_storage import SQLMetricsStorage

logger = logging.getLogger(__name__)


def _get_rollup(args: Dict[str, str]) -> RollUp:
    rollup_arg = args.get("rollup")

    if rollup_arg is None:
        return rollup_arg

    if rollup_arg.isdigit():
        return int(rollup_arg)

    if rollup_arg == "auto":
        return cast(Literal["auto"], rollup_arg)

    raise ValueError("Incorrect value for rollup. Expected an integer or 'auto'.")


@sematic_api.route("/api/v1/metrics/<metric_name>", methods=["GET"])
@authenticate
def get_metric_endpoint(user: Optional[User], metric_name: str) -> flask.Response:
    metrics_storage = SQLMetricsStorage()

    from_time_ts = float(flask.request.args.get("from_time", 0))
    to_time_ts = float(flask.request.args.get("to_time", time.time()))

    try:
        labels: Dict = json.loads(flask.request.args.get("labels", "{}"))
    except Exception as e:
        return jsonify_error(
            f"Unable to deserialize labels: {e}", HTTPStatus.BAD_REQUEST
        )

    try:
        rollup = _get_rollup(flask.request.args)
    except ValueError as e:
        return jsonify_error(str(e), HTTPStatus.BAD_REQUEST)

    filter = MetricsFilter(
        name=metric_name,
        from_time=datetime.datetime.fromtimestamp(from_time_ts),
        to_time=datetime.datetime.fromtimestamp(to_time_ts),
        labels=labels,
    )

    try:
        group_bys = [
            GroupBy(value)
            for value in flask.request.args.get("group_by", "").split(",")
            if len(value) > 0
        ]
    except ValueError:
        options = ", ".join([gb.name for gb in GroupBy])
        return jsonify_error(
            f"Unrecognized group_by. Options are: {options}", HTTPStatus.BAD_REQUEST
        )

    try:
        series = metrics_storage.get_aggregated_metrics(filter, group_bys, rollup)
    except NoMetricError as e:
        return jsonify_error(str(e), HTTPStatus.NOT_FOUND)

    return flask.jsonify(content=series)


@sematic_api.route("/api/v1/metrics", methods=["POST"])
@authenticate
def log_metric_endpoint(user: Optional[User]) -> flask.Response:
    plugin_class = get_metrics_storage_plugins(default=[SQLMetricsStorage])[0]

    plugin = plugin_class()

    payload: Dict[str, Any] = flask.request.json  # type: ignore

    metric_points = []

    for metric_point_ in payload.get("metric_points", []):
        metric_point = MetricPoint.from_json_encodable(metric_point_)
        if user is not None:
            metric_point.labels["user_id"] = user.id

        metric_points.append(metric_point)

    plugin.store_metrics(metric_points)

    # broadcast_metrics_update(metric_points, user)

    return flask.jsonify({})


@sematic_api.route("/api/v1/metrics", methods=["GET"])
@authenticate
def list_metrics_endpoint(user: Optional[User]) -> flask.Response:
    try:
        labels: Dict = json.loads(flask.request.args.get("labels", "{}"))
    except Exception as e:
        return jsonify_error(
            f"Unable to deserialize labels: {e}", HTTPStatus.BAD_REQUEST
        )

    metrics_storage = SQLMetricsStorage()

    metric_names = metrics_storage.get_metrics(labels)

    return flask.jsonify(dict(content=metric_names))


class MetricEvent(enum.IntEnum):
    run_created = 1
    run_state_changed = 0


_METRICS: Dict[MetricEvent, List[Type[AbstractSystemMetric]]] = {
    MetricEvent.run_created: [
        RunCountMetric,
    ],
    MetricEvent.run_state_changed: [
        FuncSuccessRateMetric,
        FuncEffectiveRuntimeMetric,
    ],
}


def save_event_metrics(
    event: MetricEvent, runs: List[Run], user: Optional[User] = None
):
    """
    Compute and store System Metrics associated with a particular metric event.
    """
    if len(runs) == 0:
        return

    metric_points: List[MetricPoint] = []

    for metric_class in _METRICS[event]:
        metric = metric_class()
        for run in runs:
            metric_point = metric.make_metric_point(run, user)

            if metric_point is None:
                continue

            logging.info(
                "Generated metric %s for run %s with value %s",
                metric.get_full_name(),
                run.id,
                metric_point.value,
            )

            metric_points.append(metric_point)

    _store_metrics(metric_points)


def _store_metrics(metric_points: List[MetricPoint]):
    for plugin_class in get_metrics_storage_plugins(default=[SQLMetricsStorage]):
        logging.info("Saving metrics to %s", plugin_class.get_path())  # type: ignore
        plugin_class().store_metrics(metric_points)
