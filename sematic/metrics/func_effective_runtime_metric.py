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
from sematic.utils.exceptions import DataIntegrityError


class FuncEffectiveRuntimeMetric(AbstractSystemMetric):
    """
    A system metric that measures Sematic Functions' effective runtimes.

    'Effective' because it includes the runtime of all descendant Functions.
    That time starts when `run.started_at` is set (run gets scheduled), and ends
    when `run.resolved_at` is set (all descendants have resolved).

    Only RESOLVED runs are considered, as we are interested in measuring the
    average runtime to completion. Therefore, failed or canceled runs are not
    considered.

    Cached/cloned runs are not included as their effective runtime is virtually
    zero.
    """

    @classmethod
    def _get_name(cls) -> str:
        return "func_effective_runtime"

    @classmethod
    def _get_metric_type(cls) -> MetricType:
        return MetricType.GAUGE

    def _get_value(self, run: Run) -> Optional[Tuple[datetime, float]]:
        if run.future_state != FutureState.RESOLVED.value:
            return None

        if run.original_run_id is not None:
            return None

        if run.resolved_at is None:
            raise DataIntegrityError(
                f"Run {run.id} has future_state {run.future_state} but resolved_at=None"
            )

        if run.started_at is None:
            raise DataIntegrityError(
                f"Run {run.id} has future_state {run.future_state} but started_at=None"
            )

        runtime_seconds = (run.resolved_at - run.started_at).total_seconds()

        return run.resolved_at, runtime_seconds

    def _get_backfill_query(self, session: Session) -> Query:
        return (
            session.query(Run)
            .filter(
                Run.future_state == FutureState.RESOLVED.value,
                Run.original_run_id.is_(None),
            )
            .options(joinedload(Run.root_run))
        )
