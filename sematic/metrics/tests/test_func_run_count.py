# Standard Library
from typing import List, Sequence

# Third-party
import pytest

# Sematic
from sematic.abstract_future import FutureState
from sematic.db.db import DB
from sematic.db.models.run import Run
from sematic.db.tests.fixtures import test_db
from sematic.metrics.func_run_count import FuncRunCount
from sematic.metrics.metric_point import MetricType
from sematic.plugins.abstract_metrics_storage import GroupBy, MetricSeries
from sematic.plugins.metrics_storage.sql.models.metric_value import MetricValue
from sematic.plugins.metrics_storage.sql.sql_metrics_storage import SQLMetricsStorage


def test_meta():
    assert FuncRunCount._get_name() == "run_count"
    assert FuncRunCount._get_metric_type() is MetricType.COUNT


@pytest.fixture
def twelve_runs(test_db: DB) -> List[Run]:
    runs = [
        Run(id=str(i), calculator_path=str(i), future_state=FutureState.CREATED)
        for i in range(12)
    ]
    with test_db.get_session() as session:
        session.add_all(runs)
        session.commit()
        for run in runs:
            session.refresh(run)

    return runs


def test_get_value(twelve_runs: List[Run]):
    assert FuncRunCount()._get_value(twelve_runs[0]) == (twelve_runs[0].created_at, 1)


def test_get_backfill_query(twelve_runs: List[Run], test_db: DB):
    with test_db.get_session() as session:
        query = FuncRunCount()._get_backfill_query(session)

        assert query.count() == 12


def test_backfill(twelve_runs: List[Run], test_db: DB):
    FuncRunCount().backfill()

    with test_db.get_session() as session:
        metric_values: Sequence[MetricValue] = session.query(MetricValue).all()

    assert len(metric_values) == 12

    assert all(value.value == 1 for value in metric_values)


def test_aggregation(twelve_runs: List[Run]):
    FuncRunCount().backfill()

    aggregation = FuncRunCount.aggregate(group_by=[GroupBy.calculator_path])

    assert aggregation == {
        SQLMetricsStorage.get_path(): MetricSeries(
            metric_name="sematic.run_count",
            metric_type=MetricType.COUNT.name,
            group_by_labels=["calculator_path"],
            series=[(1, (run.calculator_path)) for run in twelve_runs],
        )
    }