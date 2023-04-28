# Standard Library
from datetime import datetime
from typing import Optional, Tuple

# Third-party
from sqlalchemy.orm import Query, Session, joinedload

# Sematic
from sematic.abstract_future import FutureState
from sematic.abstract_system_metric import AbstractSystemMetric
from sematic.db.models.run import Run
from sematic.metrics.metric_point import MetricType

INCLUDED_STATES = {FutureState.RESOLVED, FutureState.FAILED, FutureState.NESTED_FAILED}


class FuncSuccessRateMetric(AbstractSystemMetric):
    """
    System Metric to measure Sematic Function's success rate.

    Success rate is defined as:

    Numerator: Number of qualifying RESOLVED runs
    Denominator: Number of qualifying (RESOLVED + FAILED + NESTED_FAILED) runs

    where qualifying runs are all non-cached, non-cloned runs.
    """

    @classmethod
    def _get_name(cls) -> str:
        return "func_success_rate"

    @classmethod
    def _get_metric_type(cls) -> MetricType:
        return MetricType.GAUGE

    def _get_value(self, run: Run) -> Optional[Tuple[datetime, float]]:
        state = FutureState(run.future_state)

        # Canceled runs result either from user action, or from the failure
        # of an upstream run. They should not be counted.
        if state not in INCLUDED_STATES:
            return None

        # Cached and cloned runs should not contribute to the success rate
        # Otherwise they would artificially inflate success counts
        if run.original_run_id is not None:
            return None

        value = 1 if state is FutureState.RESOLVED else 0
        metric_time: datetime = run.resolved_at or run.failed_at  # type: ignore

        if metric_time is None:
            self._get_logger().warning(
                "DataIntegrityWarning: Run %s has future_state %s but resolved_at=%s, "
                "failed_at=%s. Using started_at instead.",
                run.id,
                run.future_state,
                run.resolved_at,
                run.failed_at,
            )
            metric_time = run.started_at

        return metric_time, value

    def _get_backfill_query(self, session: Session) -> Query:
        return (
            session.query(Run)
            .filter(
                Run.future_state.in_([state.value for state in INCLUDED_STATES]),
                Run.original_run_id.is_(None),
            )
            .options(joinedload(Run.root_run))
        )
