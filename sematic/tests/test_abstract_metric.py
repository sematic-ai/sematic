# Standard Library
from datetime import datetime
from typing import List, Optional, Tuple
from unittest import mock

# Third-party
import pytest
from sqlalchemy.orm import Query, Session, joinedload

# Sematic
from sematic.abstract_future import FutureState
from sematic.abstract_metric import AbstractMetric, DataIntegrityError
from sematic.db.db import DB, db
from sematic.db.models.run import Run
from sematic.db.tests.fixtures import test_db
from sematic.metrics.metric_point import MetricPoint, MetricType
from sematic.plugins.abstract_metrics_storage import GroupBy, MetricSeries
from sematic.plugins.metrics_storage.sql.models.metric_value import MetricValue
from sematic.plugins.metrics_storage.sql.sql_metrics_storage import SQLMetricsStorage


class ConcreteMetric(AbstractMetric):
    @classmethod
    def _get_name(cls) -> str:
        return "concrete_metric"

    @classmethod
    def _get_metric_type(cls) -> MetricType:
        return MetricType.COUNT

    def _get_value(self, run: Run) -> Optional[Tuple[datetime, float]]:
        if run.calculator_path == "do_not_count_me":
            return None

        if run.started_at is None:
            raise DataIntegrityError("created_at is None")

        return run.started_at, 1

    def _get_backfill_query(self, session: Session) -> Query:
        return (
            session.query(Run)
            .options(joinedload(Run.root_run))
            .filter(Run.calculator_path != "do_not_query")
        )


def test_get_full_name():
    assert ConcreteMetric.get_full_name() == "sematic.concrete_metric"


@pytest.fixture
def runs(test_db: DB):
    runs = [
        Run(
            id="a",
            calculator_path="count_me",
            started_at=datetime.utcnow(),
            future_state=FutureState.CREATED,
            root_id="b",
        ),
        Run(
            id="b",
            calculator_path="count_me",
            started_at=None,
            future_state=FutureState.CREATED,
        ),
        Run(
            id="c",
            calculator_path="do_not_count_me",
            started_at=datetime.utcnow(),
            future_state=FutureState.CREATED,
        ),
        Run(
            id="d",
            calculator_path="do_not_query",
            started_at=datetime.utcnow(),
            future_state=FutureState.CREATED,
        ),
    ]
    with test_db.get_session() as session:
        session.add_all(runs)
        session.commit()
        for run in runs:
            session.refresh(run)

    return runs


def test_get_backfill_query(runs: List[Run], test_db: DB):
    with test_db.get_session() as session:
        query = ConcreteMetric()._get_backfill_query(session)

        assert query.count() == 3


def test_make_metric_point(runs: List[Run]):
    metric = ConcreteMetric()

    assert metric.make_metric_point(runs[2]) is None

    with pytest.raises(DataIntegrityError):
        metric.make_metric_point(runs[1])

    assert metric.make_metric_point(runs[0]) == MetricPoint(
        name="sematic.concrete_metric",
        value=1,
        metric_type=MetricType.COUNT,
        labels={"calculator_path": "count_me", "root_calculator_path": "count_me"},
        metric_time=runs[0].started_at,  # type: ignore
    )


@mock.patch("sematic.abstract_metric._get_root_calculator_path", return_value="foo")
def test_backfill(_, runs: List[Run], test_db: DB):
    with test_db.get_session() as session:
        assert session.query(MetricValue).count() == 0

    data_integrity_errors = ConcreteMetric().backfill()

    with test_db.get_session() as session:
        metric_values = session.query(MetricValue).all()

    assert len(metric_values) == 1
    assert metric_values[0].value == 1
    assert metric_values[0].metric_time == runs[0].started_at

    assert len(data_integrity_errors) == 1


@mock.patch("sematic.abstract_metric._get_root_calculator_path", return_value="foo")
def test_clear(_, runs: List[Run], test_db: DB):
    metric = ConcreteMetric()

    metric.backfill()

    with test_db.get_session() as session:
        assert session.query(MetricValue).count() == 1

    metric.clear()

    with test_db.get_session() as session:
        assert session.query(MetricValue).count() == 0


@mock.patch("sematic.abstract_metric._get_root_calculator_path", return_value="foo")
def test_aggregate(_, runs: List[Run], test_db: DB):
    metric = ConcreteMetric()

    metric.backfill()

    aggregation = metric.aggregate(
        labels={"calculator_path": "count_me"},
        group_by=[GroupBy.date, GroupBy.calculator_path],
    )

    assert aggregation == {
        SQLMetricsStorage.get_path(): MetricSeries(
            metric_name="sematic.concrete_metric",
            metric_type=MetricType.COUNT.name,
            group_by_labels=["date", "calculator_path"],
            series=[
                (
                    1,
                    (
                        str(runs[0].started_at.date()),  # type: ignore
                        runs[0].calculator_path,
                    ),
                )
            ],
        )
    }