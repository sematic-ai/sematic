# Sematic
from sematic.api.endpoints.metrics import MetricEvent, save_event_metrics
from sematic.db.models.run import Run
from sematic.db.tests.fixtures import (
    allow_any_run_state_transition,
    persisted_run,
    run,
    test_db,
)
from sematic.metrics.func_run_count import FuncRunCount
from sematic.metrics.metric_point import MetricType
from sematic.plugins.abstract_metrics_storage import MetricSeries
from sematic.plugins.metrics_storage.sql.sql_metrics_storage import SQLMetricsStorage


def test_run_created(persisted_run: Run):
    save_event_metrics(MetricEvent.run_created, [persisted_run])

    aggregation = FuncRunCount().aggregate(labels={}, group_by=[])

    assert aggregation == {
        SQLMetricsStorage.get_path(): MetricSeries(
            metric_name="sematic.run_count",
            metric_type=MetricType.COUNT.name,
            group_by_labels=[],
            series=[(1, ())],
        )
    }
