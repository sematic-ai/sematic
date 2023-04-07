# Standard Library
from datetime import datetime
from typing import Optional, Tuple

# Third-party
from sqlalchemy.orm import Query, Session, joinedload

# Sematic
from sematic.abstract_future import FutureState
from sematic.abstract_metric import AbstractMetric
from sematic.db.models.run import Run
from sematic.metrics.types_ import MetricScope, MetricType


class FuncEffectiveRuntime(AbstractMetric):
    @classmethod
    def get_name(cls) -> str:
        return "func_effective_runtime"

    @classmethod
    def get_metric_type(cls) -> MetricType:
        return MetricType.GAUGE

    def get_value(self, run: Run) -> Optional[Tuple[datetime, float]]:
        if run.future_state != FutureState.RESOLVED.value:
            return None

        if run.original_run_id is not None:
            return None

        if run.resolved_at is None:
            raise ValueError()

        if run.started_at is None:
            raise ValueError()

        runtime_seconds = (run.resolved_at - run.started_at).total_seconds()

        return run.resolved_at, runtime_seconds

    def get_backfill_query(self, session: Session) -> Query:
        return (
            session.query(Run)
            .filter(
                Run.future_state == FutureState.RESOLVED.value,
                Run.original_run_id.is_(None),
            )
            .options(joinedload(Run.root_run))
        )
