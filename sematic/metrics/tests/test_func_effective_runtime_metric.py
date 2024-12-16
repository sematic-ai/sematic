# Standard Library
from datetime import datetime, timedelta
from typing import List

# Third-party
import pytest

# Sematic
from sematic.abstract_future import FutureState
from sematic.db.db import DB
from sematic.db.models.run import Run
from sematic.db.tests.fixtures import run, test_db  # noqa: F401
from sematic.metrics.func_effective_runtime_metric import FuncEffectiveRuntimeMetric
from sematic.metrics.metric_point import MetricType
from sematic.plugins.abstract_metrics_storage import MetricSeries
from sematic.plugins.metrics_storage.sql.models.metric_value import MetricValue
from sematic.plugins.metrics_storage.sql.sql_metrics_storage import SQLMetricsStorage
from sematic.utils.exceptions import DataIntegrityError


_STARTED_AT = datetime.now() - timedelta(days=1)


@pytest.mark.parametrize(
    "future_state, original_run_id, started_at, resolved_at, expected_value",
    (
        (FutureState.CREATED, None, None, None, None),
        (FutureState.RESOLVED, "foo", None, None, None),
        (
            FutureState.RESOLVED,
            None,
            datetime(2023, 4, 27),
            datetime(2023, 4, 27) + timedelta(seconds=100),
            (datetime(2023, 4, 27) + timedelta(seconds=100), 100),
        ),
    ),
)
def test_get_value(
    future_state: FutureState,
    original_run_id,
    started_at,
    resolved_at,
    expected_value,
    run: Run,  # noqa: F811
):
    run.future_state = future_state.value
    run.original_run_id = original_run_id
    run.started_at = started_at
    run.resolved_at = resolved_at

    value = FuncEffectiveRuntimeMetric()._get_value(run)

    assert value == expected_value


@pytest.mark.parametrize(
    "started_at, resolved_at", ((None, None), (None, datetime.utcnow()))
)
def test_get_value_raises(run: Run, started_at, resolved_at):  # noqa: F811
    run.future_state = FutureState.RESOLVED.value  # type: ignore
    run.started_at = started_at
    run.resolved_at = resolved_at
    with pytest.raises(DataIntegrityError):
        FuncEffectiveRuntimeMetric()._get_value(run)


@pytest.fixture
def twelve_runs(test_db: DB):  # noqa: F811
    runs = [
        Run(
            id=str(i),
            future_state=FutureState.CREATED if i == 0 else FutureState.RESOLVED,
            function_path=str(i // 6),
            source_code="some code",
            original_run_id="foo" if i == 1 else None,
            resolved_at=(None if i == 2 else _STARTED_AT + timedelta(seconds=10 + i)),
            started_at=None if i == 3 else _STARTED_AT + timedelta(seconds=i),
            root_id="0",
        )
        for i in range(12)
    ]

    with test_db.get_session() as session:
        session.add_all(runs)
        session.commit()

        for run in runs:  # noqa: F402
            session.refresh(run)

    return runs


def test_get_backfill_query(twelve_runs: List[Run], test_db: DB):  # noqa: F811
    with test_db.get_session() as session:
        query = FuncEffectiveRuntimeMetric()._get_backfill_query(session)

        assert query.count() == 10


def test_backfill(twelve_runs: List[Run], test_db: DB):  # noqa: F811
    errors = FuncEffectiveRuntimeMetric().backfill()

    assert len(errors) == 2

    with test_db.get_session() as session:
        metric_values = session.query(MetricValue).all()

    assert len(metric_values) == 8

    assert all([metric_value.value == 10 for metric_value in metric_values])


def test_aggregation(twelve_runs: List[Run]):
    metric = FuncEffectiveRuntimeMetric()

    metric.backfill()

    aggregation = metric.aggregate(labels={}, group_by=[], rollup=None)

    assert aggregation == {
        SQLMetricsStorage.get_path(): MetricSeries(
            metric_name="sematic.func_effective_runtime",
            metric_type=MetricType.GAUGE.name,
            columns=[],
            series=[(10, ())],
        )
    }
