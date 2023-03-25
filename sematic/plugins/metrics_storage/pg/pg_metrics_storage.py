# Standard Library
import numbers
from collections import defaultdict
from typing import Dict, List, Optional, Type

# Sematic
from sematic.abstract_plugin import (
    SEMATIC_PLUGIN_AUTHOR,
    AbstractPlugin,
    AbstractPluginSettingsVar,
    PluginVersion,
)
from sematic.db.db import db
from sematic.plugins.abstract_metrics_storage import (
    AbstractMetricsStorage,
    AggregatedMetrics,
    AggregatedMetricsBucket,
    AggregationOptions,
    MetricPoint,
    MetricsFilter,
    MetricType,
)
from sematic.plugins.metrics_storage.pg.db.models.metric import Metric

_PLUGIN_VERSION = (0, 1, 0)


class PGMetricsStorageSettingsVar(AbstractPluginSettingsVar):
    pass


class PGMetricsStorage(AbstractMetricsStorage, AbstractPlugin):
    @staticmethod
    def get_author() -> str:
        return SEMATIC_PLUGIN_AUTHOR

    @staticmethod
    def get_version() -> PluginVersion:
        return _PLUGIN_VERSION

    @classmethod
    def get_settings_vars(cls) -> Type[AbstractPluginSettingsVar]:
        return PGMetricsStorageSettingsVar

    def store_metrics(self, metric_points: List[MetricPoint]) -> None:
        metrics = list(map(_make_metric, metric_points))
        with db().get_session() as session:
            session.add_all(metrics)
            session.commit()

    def get_metrics(self, filters: MetricsFilter) -> List[MetricPoint]:
        filter_predicates = [
            Metric.scope == filters.scope.value,
            Metric.scope_id == filters.scope_id,
            Metric.measured_at > filters.from_time,
            Metric.measured_at <= filters.to_time,
        ]

        if filters.name is not None:
            filter_predicates.append(Metric.name == filters.name)

        with db().get_session() as session:
            metrics = session.query(Metric).filter(*filter_predicates).all()

        return list(map(_make_metric_point, metrics))

    def get_aggregated_metrics(
        self, filters: MetricsFilter, options: Optional[AggregationOptions] = None
    ):
        metrics = self.get_metrics(filters)

        aggregations: Dict[str, Dict[str, numbers.Real]] = dict()

        gauge_counts: Dict[str, Dict[str, int]] = defaultdict(
            lambda: defaultdict(lambda: 0)
        )

        for metric in metrics:
            if metric.metric_type is MetricType.COUNT:
                base = aggregations.get(
                    metric.name, defaultdict(lambda: 0)  # type: ignore
                )
                for key, value in metric.value.items():
                    if not isinstance(value, (int, float)):
                        raise ValueError(
                            "COUNT metric can only be of type (int, float)"
                        )

                    base[key] += value

                aggregations[metric.name] = base

            if metric.metric_type is MetricType.GAUGE:
                base = aggregations.get(
                    metric.name, defaultdict(lambda: 0)  # type: ignore
                )
                for key, value in metric.value.items():
                    if not isinstance(value, (int, float)):
                        raise ValueError(
                            "GAUGE metric can only be of type (int, float)"
                        )

                    count = gauge_counts[metric.name][key]
                    base[key] = (base[key] * count + value) / (count + 1)
                    gauge_counts[metric.name][key] += 1

                aggregations[metric.name] = base

            # ToDo: histogram

        return AggregatedMetrics(
            filters=filters,
            options=options,
            totals=AggregatedMetricsBucket(
                from_time=filters.from_time,
                to_time=filters.to_time,
                aggregations=aggregations,
            ),
            buckets=[],
        )


def _make_metric(metric_point: MetricPoint) -> Metric:
    return Metric(
        name=metric_point.name,
        value=metric_point.value,
        scope=metric_point.scope,
        scope_id=metric_point.scope_id,
        metric_type=metric_point.metric_type,
        annotations=metric_point.annotations,
        measured_at=metric_point.measured_at,
    )


def _make_metric_point(metric: Metric) -> MetricPoint:
    return MetricPoint(
        name=metric.name,
        value=metric.value,
        scope=metric.scope,
        scope_id=metric.scope_id,
        metric_type=metric.metric_type,
        annotations=metric.annotations,
        measured_at=metric.measured_at,
    )
