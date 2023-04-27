# Standard Library
from datetime import datetime
from typing import List, Optional

# Third-party
import pytest

# Sematic
from sematic.abstract_future import FutureState
from sematic.db.db import DB
from sematic.db.models.run import Run
from sematic.db.tests.fixtures import run, test_db  # noqa: F401
from sematic.metrics.func_success_rate_metric import FuncSuccessRateMetric
from sematic.metrics.metric_point import MetricType
from sematic.plugins.abstract_metrics_storage import MetricSeries
from sematic.plugins.metrics_storage.sql.models.metric_value import MetricValue
from sematic.plugins.metrics_storage.sql.sql_metrics_storage import SQLMetricsStorage


@pytest.mark.parametrize(
    "future_state, original_run_id, resolved_at, failed_at, started_at, expected_value",
    (
        (FutureState.CANCELED, None, None, None, None, None),
        (FutureState.RESOLVED, "foo", None, None, None, None),
        (FutureState.CANCELED, None, None, None, None, None),
        (
            FutureState.RESOLVED,
            None,
            datetime(2023, 4, 26),
            None,
            None,
            (datetime(2023, 4, 26), 1),
        ),
        (
            FutureState.FAILED,
            None,
            None,
            datetime(2023, 4, 26),
            None,
            (datetime(2023, 4, 26), 0),
        ),
        (
            FutureState.NESTED_FAILED,
            None,
            None,
            datetime(2023, 4, 26),
            None,
            (datetime(2023, 4, 26), 0),
        ),
        (
            FutureState.RESOLVED,
            None,
            None,
            None,
            datetime(2023, 4, 26),
            (datetime(2023, 4, 26), 1),
        ),
    ),
)
def test_get_value(
    future_state: FutureState,
    original_run_id: Optional[str],
    resolved_at: Optional[datetime],
    failed_at: Optional[datetime],
    started_at: Optional[datetime],
    expected_value,
    run: Run,  # noqa: F811
):
    run.future_state = future_state.value
    run.original_run_id = original_run_id
    run.resolved_at = resolved_at
    run.failed_at = failed_at
    run.started_at = started_at

    assert FuncSuccessRateMetric()._get_value(run) == expected_value


@pytest.fixture
def twelve_runs(test_db: DB) -> List[Run]:  # noqa: F811
    states = [
        FutureState.CREATED,
        FutureState.RESOLVED,
        FutureState.FAILED,
        FutureState.NESTED_FAILED,
    ]
    runs = [
        Run(
            id=str(i),
            future_state=states[i // 3],
            original_run_id=str(i) if i % 3 == 0 else None,
            root_id="0",
            started_at=datetime.utcnow(),
        )
        for i in range(12)
    ]

    with test_db.get_session() as session:
        session.add_all(runs)
        session.commit()
        for run in runs:  # noqa: F402
            session.refresh(run)

    return runs


def test_backfill_query(twelve_runs: List[Run], test_db: DB):  # noqa: F811
    with test_db.get_session() as session:
        query = FuncSuccessRateMetric()._get_backfill_query(session)

        # 1 in 4 is CREATED (non terminal state)
        # 1 in 3 is cached
        # (3/4) * (2/3) * 12 = 6
        assert query.count() == 6


def test_backfill(twelve_runs: List[Run], test_db: DB):  # noqa: F811
    FuncSuccessRateMetric().backfill()

    with test_db.get_session() as session:
        metric_values = session.query(MetricValue).all()

    assert len(metric_values) == 6

    assert (
        len([metric_value for metric_value in metric_values if metric_value.value == 1])
        == 2
    )

    assert (
        len([metric_value for metric_value in metric_values if metric_value.value == 0])
        == 4
    )


def test_aggregation(twelve_runs: List[Run]):
    metric = FuncSuccessRateMetric()

    metric.backfill()

    aggregation = metric.aggregate(labels={}, group_by=[], rollup=None)

    assert aggregation == {
        SQLMetricsStorage.get_path(): MetricSeries(
            metric_name="sematic.func_success_rate",
            metric_type=MetricType.GAUGE.name,
            columns=[],
            series=[(1.0 / 3, ())],
        )
    }
