# Standard Library
import datetime
import json
import time
from http import HTTPStatus
from typing import Dict, Optional

# Third-party
import flask

# Sematic
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate
from sematic.api.endpoints.request_parameters import jsonify_error
from sematic.db.models.user import User
from sematic.plugins.abstract_metrics_storage import (
    GroupBy,
    MetricsFilter,
    NoMetricError,
    get_metrics_storage_plugins,
)
from sematic.plugins.metrics_storage.pg.pg_metrics_storage import PGMetricsStorage


@sematic_api.route("/api/v1/metrics/<metric_name>", methods=["GET"])
@authenticate
def get_metric_endpoint(user: Optional[User], metric_name: str) -> flask.Response:
    plugin_class = get_metrics_storage_plugins(default=[PGMetricsStorage])[0]

    plugin = plugin_class()

    from_time_ts = float(flask.request.args.get("from_time", 0))
    to_time_ts = float(flask.request.args.get("to_time", time.time()))

    try:
        labels: Dict = json.loads(flask.request.args.get("labels", "{}"))
    except Exception as e:
        return jsonify_error(
            f"Unable to deserialize labels: {e}", HTTPStatus.BAD_REQUEST
        )

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
            f"Unrecognized group_by. Options are {options}", HTTPStatus.BAD_REQUEST
        )

    try:
        series = plugin.get_aggregated_metrics(filter, group_bys)
    except NoMetricError as e:
        return jsonify_error(str(e), HTTPStatus.NOT_FOUND)

    return flask.jsonify(content=series)
