# Standard Library
from datetime import datetime
from typing import Optional, Tuple

# Third-party
from sqlalchemy.orm import Query, Session, joinedload

# Sematic
from sematic.abstract_metric import AbstractMetric
from sematic.db.models.run import Run
from sematic.metrics.types_ import MetricType


class FuncRunCount(AbstractMetric):
    @classmethod
    def get_name(self) -> str:
        return "run_count"

    @classmethod
    def get_metric_type(self) -> MetricType:
        return MetricType.COUNT

    def get_value(self, run: Run) -> Optional[Tuple[datetime, float]]:
        return run.created_at, 1

    def get_backfill_query(self, session: Session) -> Query:
        return session.query(Run).options(joinedload(Run.root_run))
