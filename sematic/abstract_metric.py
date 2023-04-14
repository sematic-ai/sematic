# Standard Library
import abc
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

# Third-party
import sqlalchemy.orm

# Sematic
from sematic.abstract_plugin import PluginScope
from sematic.db.db import db
from sematic.db.models.run import Run
from sematic.db.queries import get_calculator_path
from sematic.metrics.metric_point import MetricPoint, MetricType
from sematic.plugins.abstract_metrics_storage import (
    AbstractMetricsStorage,
    GroupBy,
    MetricSeries,
    MetricsFilter,
    get_metrics_storage_plugins,
)
from sematic.plugins.metrics_storage.sql.sql_metrics_storage import SQLMetricsStorage


class DataIntegrityError(Exception):
    pass


class AbstractMetric(abc.ABC):
    """
    Abstract base class to represent a System Metric.
    """

    NAME_PREFIX = "sematic"

    _plugins: Optional[List[AbstractMetricsStorage]] = None

    @classmethod
    def _get_logger(cls) -> logging.Logger:
        return logging.getLogger(cls.get_full_name())

    @classmethod
    @abc.abstractmethod
    def _get_name(cls) -> str:
        pass

    @classmethod
    @abc.abstractmethod
    def _get_metric_type(cls) -> MetricType:
        pass

    @abc.abstractmethod
    def _get_value(self, run: Run) -> Optional[Tuple[datetime, float]]:
        """
        The metric's value for the given run.

        Parameters
        ----------
        run: Run

        Returns
        -------
        Optional[Tuple[datetime, float]]
            If no metric value should be recorded for run, return None.
            Otherwise, return a tuple of metric time and value.
        """
        pass

    @abc.abstractmethod
    def _get_backfill_query(
        self, session: sqlalchemy.orm.Session
    ) -> sqlalchemy.orm.Query:
        """
        The query to be used to backfill this metric.
        """
        pass

    @classmethod
    def get_full_name(cls) -> str:
        return ".".join([cls.NAME_PREFIX, cls._get_name()])

    def make_metric_point(self, run: Run) -> Optional[MetricPoint]:
        measured_value = self._get_value(run)

        if measured_value is None:
            return None

        metric_time, value = measured_value

        metric_point = MetricPoint(
            name=self.get_full_name(),
            value=value,
            metric_time=metric_time,
            metric_type=self._get_metric_type(),
            labels={
                # "run_id": run.id,
                "calculator_path": run.calculator_path,
                # "root_id": run.root_id,
                "root_calculator_path": _get_root_calculator_path(run),
            },
        )

        return metric_point

    def backfill(self) -> List[DataIntegrityError]:
        logger = self._get_logger()
        logger.info("Starting backfill...")

        with db().get_session() as session:
            query = self._get_backfill_query(session)

            count = query.count()
            print(count)
            PAGE_SIZE = 100

            pages = count // PAGE_SIZE + 1

            logger.info("Querying %s records in %s pages", count, pages)

            metric_points: List[MetricPoint] = []

            integrity_errors: List[DataIntegrityError] = []

            for i in range(pages):
                records = query.limit(PAGE_SIZE).offset(i * PAGE_SIZE).all()
                print(len(records))
                for record in records:
                    try:
                        metric_point = self.make_metric_point(record)
                    except DataIntegrityError as e:
                        logger.error(str(e))
                        integrity_errors.append(e)
                        continue

                    if metric_point is None:
                        continue

                    metric_points.append(metric_point)

        self.clear()

        for plugin in self.plugins:
            logger.info("Using plugin %s", plugin.__class__.__name__)
            print(plugin.get_path(), metric_points)
            plugin.store_metrics(metric_points)

        if len(integrity_errors) > 0:
            logger.warning(
                "Found %s fatal data integrity errors in %s runs.",
                len(integrity_errors),
                count,
            )

        return integrity_errors

    def clear(self):
        logger = self._get_logger()

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
    ) -> Dict[str, MetricSeries]:
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
                    PluginScope.METRICS_WRITE, default=[SQLMetricsStorage]
                )
            ]

        return self._plugins


def _get_root_calculator_path(run: Run) -> str:
    # Sometimes root_run is already loaded by the query, sometimes not.
    try:
        return run.root_run.calculator_path
    except sqlalchemy.orm.exc.DetachedInstanceError:
        return get_calculator_path(run.root_id)