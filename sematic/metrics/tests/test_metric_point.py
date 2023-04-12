# Standard Library
import datetime
import json

# Sematic
from sematic.metrics.metric_point import MetricPoint, MetricType


def test_to_json_encodable():
    metric_point = MetricPoint(
        name="foo",
        value=0.123,
        metric_type=MetricType.GAUGE,
        labels={"foo": "bar"},
        metric_time=datetime.datetime.utcnow(),
    )

    assert (
        MetricPoint.from_json_encodable(
            json.loads(json.dumps(metric_point.to_json_encodable()))
        )
        == metric_point
    )
