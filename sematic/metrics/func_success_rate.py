# Standard Library
from datetime import datetime
from typing import Optional, Tuple

# Third-party
from sqlalchemy.orm import Query, Session, joinedload

# Sematic
from sematic.abstract_future import FutureState
from sematic.abstract_metric import AbstractMetric
from sematic.db.models.run import Run
from sematic.metrics.types_ import MetricType

FINAL_STATES = {FutureState.RESOLVED, FutureState.FAILED, FutureState.NESTED_FAILED}


class FuncSuccessRate(AbstractMetric):
    @classmethod
    def get_name(cls) -> str:
        return "func_success_rate"

    @classmethod
    def get_metric_type(cls) -> MetricType:
        return MetricType.GAUGE

    def get_value(self, run: Run) -> Optional[Tuple[datetime, float]]:
        state = FutureState(run.future_state)

        if not state.is_terminal():
            return None

        if run.original_run_id is not None:
            return None

        if state is FutureState.CANCELED:
            return None

        value = 1 if state is FutureState.RESOLVED else 0
        measured_at: datetime = run.resolved_at or run.failed_at  # type: ignore

        return measured_at, value

    def get_backfill_query(self, session: Session) -> Query:
        return (
            session.query(Run)
            .filter(
                Run.future_state.in_([state.value for state in FINAL_STATES]),
                Run.original_run_id.is_(None),
            )
            .options(joinedload(Run.root_run))
        )
