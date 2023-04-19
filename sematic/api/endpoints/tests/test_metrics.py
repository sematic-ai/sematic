# Sematic
from sematic.api.endpoints.metrics import MetricEvent, save_event_metrics
from sematic.db.models.run import Run
from sematic.db.tests.fixtures import (  # noqa: F401
    allow_any_run_state_transition,
    persisted_run,
    run,
    test_db,
)
from sematic.metrics.metric_point import MetricType
from sematic.metrics.run_count_metric import RunCountMetric
from sematic.plugins.abstract_metrics_storage import MetricSeries
from sematic.plugins.metrics_storage.sql.sql_metrics_storage import SQLMetricsStorage


def test_run_created(persisted_run: Run):  # noqa: F811
    save_event_metrics(MetricEvent.run_created, [persisted_run])

    aggregation = RunCountMetric().aggregate(labels={}, group_by=[], rollup=None)

    assert aggregation == {
        SQLMetricsStorage.get_path(): MetricSeries(
            metric_name="sematic.run_count",
            metric_type=MetricType.COUNT.name,
            columns=[],
            series=[(1, ())],
        )
    }
