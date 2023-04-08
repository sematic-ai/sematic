# Standard Library
import abc
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

# Third-party
import sqlalchemy.orm

# Sematic
from sematic.db.db import db
from sematic.db.models.run import Run
from sematic.db.queries import get_calculator_path
from sematic.metrics.types_ import MetricPoint, MetricType
from sematic.plugins.abstract_metrics_storage import (
    AbstractMetricsStorage,
    GroupBy,
    MetricsFilter,
    get_metrics_storage_plugins,
)
from sematic.plugins.metrics_storage.pg.pg_metrics_storage import PGMetricsStorage


class DataIntegrityError(Exception):
    pass


class AbstractMetric(abc.ABC):

    NAME_PREFIX = "sematic"
    _plugins: Optional[List[AbstractMetricsStorage]] = None

    @classmethod
    def get_logger(cls) -> logging.Logger:
        return logging.getLogger(cls.get_full_name())

    @classmethod
    @abc.abstractmethod
    def get_name(cls) -> str:
        pass

    @classmethod
    @abc.abstractmethod
    def get_metric_type(cls) -> MetricType:
        pass

    @abc.abstractmethod
    def get_value(self, run: Run) -> Optional[Tuple[datetime, float]]:
        pass

    @abc.abstractmethod
    def get_backfill_query(
        self, session: sqlalchemy.orm.Session
    ) -> sqlalchemy.orm.Query:
        pass

    def save_metric(self, object: Any):
        metric_point = self.make_metric_point(object)

        if metric_point is None:
            return

        for plugin in self.plugins:
            plugin.store_metrics([metric_point])

    @classmethod
    def get_full_name(cls) -> str:
        return ".".join([cls.NAME_PREFIX, cls.get_name()])

    def make_metric_point(self, run: Run) -> Optional[MetricPoint]:
        measured_value = self.get_value(run)

        if measured_value is None:
            return None

        metric_time, value = measured_value

        metric_point = MetricPoint(
            name=self.get_full_name(),
            value=value,
            metric_time=metric_time,
            metric_type=self.get_metric_type(),
            labels={
                "run_id": run.id,
                "calculator_path": run.calculator_path,
                "root_id": run.root_id,
                "root_calculator_path": _get_root_calculator_path(run),
            },
        )

        return metric_point

    def backfill(self):
        logger = self.get_logger()
        logger.info("Starting backfill...")

        with db().get_session() as session:
            query = self.get_backfill_query(session)

            count = query.count()

            PAGE_SIZE = 100

            pages = count // PAGE_SIZE + 1

            logger.info("Querying %s records in %s pages", count, pages)

            metric_points: List[MetricPoint] = []

            integrity_error_count = 0

            for i in range(pages):
                records = query.limit(PAGE_SIZE).offset(i * PAGE_SIZE).all()
                for record in records:
                    try:
                        metric_point = self.make_metric_point(record)
                    except DataIntegrityError as e:
                        logger.error(str(e))
                        integrity_error_count += 1
                        continue

                    if metric_point is None:
                        continue

                    metric_points.append(metric_point)

        self.clear()

        for plugin in self.plugins:
            logger.info("Using plugin %s", plugin.__class__.__name__)
            plugin.store_metrics(metric_points)

        if integrity_error_count > 0:
            logger.warning(
                "Found %s fatal data integrity errors in %s runs.",
                integrity_error_count,
                count,
            )

    def clear(self, scope_id: Optional[str] = None):
        logger = self.get_logger()

        filter = MetricsFilter(
            name=self.get_full_name(),
            from_time=datetime.fromtimestamp(0),
            to_time=datetime.utcnow(),
            labels={},
        )

        for plugin in self.plugins:
            logger.info("Using plugin %s", plugin.__class__.__name__)
            plugin.clear_metrics(filter)

    def aggregate(
        self,
        labels: Dict[str, Union[int, float, str, bool, None]],
        group_by: List[GroupBy],
    ):
        filters = MetricsFilter(
            name=self.get_full_name(),
            from_time=datetime.fromtimestamp(0),
            to_time=datetime.utcnow(),
            labels=labels,
        )

        return {
            plugin.get_path(): plugin.get_aggregated_metrics(filters, group_by)
            for plugin in self.plugins
        }

    @property
    def plugins(self) -> List[AbstractMetricsStorage]:
        if self._plugins is None:
            self._plugins: List[AbstractMetricsStorage] = [
                plugin_class()
                for plugin_class in get_metrics_storage_plugins(
                    default=[PGMetricsStorage]
                )
            ]

        return self._plugins


def _get_root_calculator_path(run: Run) -> str:
    try:
        return run.root_run.calculator_path
    except sqlalchemy.orm.exc.DetachedInstanceError:
        return get_calculator_path(run.root_id)
