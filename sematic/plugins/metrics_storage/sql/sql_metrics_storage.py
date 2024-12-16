# Standard Library
import logging
import math
from typing import Dict, List, Sequence, Tuple, Type

# Third-party
import sqlalchemy.exc
from sqlalchemy import Integer, func
from sqlalchemy import cast as sql_cast

# Sematic
from sematic.abstract_plugin import (
    SEMATIC_PLUGIN_AUTHOR,
    AbstractPlugin,
    AbstractPluginSettingsVar,
    PluginVersion,
)
from sematic.config.config import SQLITE_WARNING_MESSAGE
from sematic.db.db import db
from sematic.metrics.metric_point import MetricPoint, MetricsLabels, MetricType
from sematic.plugins.abstract_metrics_storage import (
    AbstractMetricsStorage,
    GroupBy,
    MetricSeries,
    MetricsFilter,
    NoMetricError,
    RollUp,
)
from sematic.plugins.metrics_storage.sql.models.metric_label import MetricLabel
from sematic.plugins.metrics_storage.sql.models.metric_value import MetricValue
from sematic.utils.hashing import get_str_sha1_digest


logger = logging.getLogger(__name__)


_PLUGIN_VERSION = (0, 1, 0)


class SQLMetricsStorageSettingsVar(AbstractPluginSettingsVar):
    pass


_MAX_SERIES_POINTS = 300


class SQLMetricsStorage(AbstractMetricsStorage, AbstractPlugin):
    """
    Metrics storage plug-in to store metrics values in a SQL database (SQLite
    3.38.0+ and PostgreSQL).
    """

    @staticmethod
    def get_author() -> str:
        return SEMATIC_PLUGIN_AUTHOR

    @staticmethod
    def get_version() -> PluginVersion:
        return _PLUGIN_VERSION

    @classmethod
    def get_settings_vars(cls) -> Type[AbstractPluginSettingsVar]:
        return SQLMetricsStorageSettingsVar

    def store_metrics(self, metric_points: Sequence[MetricPoint]) -> None:
        logger.info("Storing %s metric points", len(metric_points))

        metric_values: List[MetricValue] = []
        metric_labels: Dict[str, MetricLabel] = dict()

        for metric_point in metric_points:
            metric_label = _make_metric_label(metric_point)
            metric_labels[metric_label.metric_id] = metric_label

            metric_value = MetricValue(
                metric_id=metric_label.metric_id,
                value=metric_point.value,
                metric_time=metric_point.metric_time,
            )
            metric_values.append(metric_value)

        with db().get_session() as session:
            existing_metric_ids = (
                session.query(MetricLabel.metric_id)  # type: ignore
                .filter(MetricLabel.metric_id.in_(metric_labels.keys()))
                .all()
            )

        existing_metric_ids = {row[0] for row in existing_metric_ids}  # type: ignore

        new_metric_labels = [
            metric_label
            for metric_label in metric_labels.values()
            if metric_label.metric_id not in existing_metric_ids
        ]

        with db().get_session() as session:
            session.add_all(new_metric_labels)
            session.add_all(metric_values)
            session.commit()

    def get_metrics(self, labels: MetricsLabels) -> Tuple[str, ...]:
        with db().get_session() as session:
            metric_names = (
                session.query(MetricLabel.metric_name)  # type: ignore
                .group_by(MetricLabel.metric_name)
                .filter(*_make_predicates_from_labels(labels))
                .all()
            )

        return tuple(row[0] for row in metric_names)

    def get_aggregated_metrics(
        self,
        filter: MetricsFilter,
        group_by: Sequence[GroupBy],
        rollup: RollUp,
    ) -> MetricSeries:
        # Early check as later queries fail when there are no rows.
        try:
            with db().get_session() as session:
                session.query(MetricLabel.metric_id).filter(  # type: ignore
                    MetricLabel.metric_name == filter.name
                ).limit(1).one()
        except sqlalchemy.exc.NoResultFound:
            raise NoMetricError(filter.name, self.get_path())

        predicates = [
            MetricLabel.metric_id == MetricValue.metric_id,
            MetricLabel.metric_name == filter.name,
            MetricValue.metric_time >= filter.from_time,
            MetricValue.metric_time < filter.to_time,
        ]

        predicates += _make_predicates_from_labels(filter.labels)

        select_fields = [
            MetricLabel.metric_name,
            MetricLabel.metric_type,
            func.sum(MetricValue.value),
            func.count(MetricValue.value),
        ]

        n_basic_fields = len(select_fields)

        extra_field_names = []

        group_by_clauses = [
            MetricLabel.metric_name,
            MetricLabel.metric_type,
        ]
        order_by_field = MetricValue.metric_time

        time_range = filter.to_time - filter.from_time
        # Ceil to make sure we always have fewer than _MAX_SERIES_POINTS
        interval_seconds = math.ceil(time_range.total_seconds() / _MAX_SERIES_POINTS)

        if isinstance(rollup, int):
            interval_seconds = max(interval_seconds, rollup)
            field_ = (
                sql_cast(
                    func.extract("epoch", MetricValue.metric_time) / interval_seconds,
                    Integer,
                )
                * interval_seconds
            )
            select_fields.append(field_)
            group_by_clauses.append(field_)  # type: ignore
            extra_field_names.append("timestamp")
            order_by_field = field_  # type: ignore

        for gb in group_by:
            extra_field_names.append(gb.value)
            field_ = MetricLabel.metric_labels[gb.value].astext

            select_fields.append(field_)
            group_by_clauses.append(field_)  # type: ignore

        try:
            with db().get_session() as session:
                query = session.query(*select_fields).filter(  # type: ignore
                    *predicates
                )

                if len(group_by_clauses) > 0:
                    query = query.group_by(*group_by_clauses)  # type: ignore

                if rollup == "auto":
                    field_ = func.extract(  # type: ignore
                        "epoch",
                        MetricValue.metric_time,
                    )
                    query = query.order_by(field_).add_columns(field_)  # type: ignore
                    record_count = query.group_by(field_).count()  # type: ignore

                    if record_count > _MAX_SERIES_POINTS:
                        field_ = (
                            sql_cast(field_ / interval_seconds, Integer)
                            * interval_seconds
                        )
                    order_by_field = field_  # type: ignore

                    query = query.add_columns(field_).group_by(field_)  # type: ignore
                    extra_field_names.append("timestamp")
                else:
                    query = query.order_by(MetricValue.metric_time)  # type: ignore
                records = query.order_by(order_by_field).all()  # type: ignore
        except sqlalchemy.exc.OperationalError as e:
            # User has old SQLite version that does not support querying JSONB fields.
            if str(e).startswith('(sqlite3.OperationalError) near ">>"'):
                logger.error(SQLITE_WARNING_MESSAGE)
                records = []
            else:
                raise e

        output = MetricSeries(metric_name=filter.name, columns=extra_field_names)

        for record in records:
            _, metric_type, metric_sum, metric_count = record[:n_basic_fields]
            output.metric_type = MetricType(metric_type).name
            metric_value: float = metric_sum
            if metric_type == MetricType.GAUGE.value:
                metric_value = float(metric_sum) / (metric_count or 1)

            output_labels = tuple(str(label) for label in record[n_basic_fields:])
            output.series.append((metric_value, output_labels))

        return output

    def clear_metrics(self, filter: MetricsFilter) -> None:
        labels_predicates = _make_predicates_from_labels(filter.labels)

        with db().get_session() as session:
            metric_ids: Sequence[str] = (
                session.query(MetricLabel.metric_id)  # type: ignore
                .filter(MetricLabel.metric_name == filter.name, *labels_predicates)
                .all()
            )
            metric_ids = {row[0] for row in metric_ids}  # type: ignore

            session.query(MetricValue).filter(
                MetricValue.metric_id.in_(metric_ids),  # type: ignore
                MetricValue.metric_time >= filter.from_time,
                MetricValue.metric_time < filter.to_time,
            ).delete()
            session.commit()


def _make_metric_label(metric_point: MetricPoint) -> MetricLabel:
    metric_label = MetricLabel(
        metric_name=metric_point.name,
        metric_type=metric_point.metric_type,
        metric_labels=metric_point.labels,
    )

    labels_hash_dict = dict(
        __name__=metric_label.metric_name,
        metric_type=metric_label.metric_type.value,
        **metric_label.metric_labels,
    )

    labels_hash_str = ",".join(
        [f"{key}:{labels_hash_dict[key]}" for key in sorted(labels_hash_dict)]
    )

    labels_hash = get_str_sha1_digest(labels_hash_str)
    metric_label.metric_id = labels_hash

    return metric_label


def _make_predicates_from_labels(labels: MetricsLabels):
    predicates = [
        MetricLabel.metric_labels[key].astext == str(value)  # type: ignore
        for key, value in labels.items()
        if key != "root"
    ]
    if "root" in labels:
        value = labels["root"]
        if value is True:
            predicates.append(
                MetricLabel.metric_labels["run_id"].astext  # type: ignore
                == MetricLabel.metric_labels["root_id"].astext  # type: ignore
            )
        elif value is False:
            predicates.append(
                MetricLabel.metric_labels["run_id"].astext  # type: ignore
                != MetricLabel.metric_labels["root_id"].astext  # type: ignore
            )

    return predicates
