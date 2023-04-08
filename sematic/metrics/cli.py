# Standard Library
import functools
import logging
from typing import Dict, List, Optional, Set, Type, Union

# Third-party
import click

# Sematic
from sematic.abstract_metric import AbstractMetric
from sematic.config.config import switch_env
from sematic.metrics.func_effective_runtime import FuncEffectiveRuntime
from sematic.metrics.func_run_count import FuncRunCount
from sematic.metrics.func_success_rate import FuncSuccessRate
from sematic.plugins.abstract_metrics_storage import GroupBy, MetricsLabels

_METRICS: Set[Type[AbstractMetric]] = {
    FuncRunCount,
    FuncEffectiveRuntime,
    FuncSuccessRate,
}

_METRICS_BY_NAME: Dict[str, Type[AbstractMetric]] = {
    metric.get_full_name(): metric for metric in _METRICS
}


def common_options(f):
    options = [
        click.option(
            "--env",
            "env",
            type=click.STRING,
            help="Environment in which to run migrations.",
            default="local",
        ),
        click.option(
            "--verbose", "verbose", is_flag=True, default=False, help="INFO log level"
        ),
    ]
    return functools.reduce(lambda x, opt: opt(x), options, f)


@click.group("migrate")
@common_options
def main(env: str, verbose: bool):
    _apply_common_options(env, verbose)


def _apply_common_options(env, verbose):
    switch_env(env)

    if verbose:
        logging.basicConfig(
            level=logging.INFO,
            format="%(levelname)s: %(asctime)s %(name)s: %(message)s",
        )


@main.command("backfill", short_help="Backfill metric")
@common_options
@click.argument("metric_name", type=click.STRING)
def _backfill(env: str, verbose: bool, metric_name: str):
    _apply_common_options(env, verbose)
    backfill_metric(metric_name)


def _get_metric(metric_name: str) -> AbstractMetric:
    if metric_name not in _METRICS_BY_NAME:
        available_metrics_str = "\n".join(_METRICS_BY_NAME.keys())
        raise ValueError(
            f"Unknown metric: {metric_name}. Choose from:\n{available_metrics_str}"
        )

    metric_class = _METRICS_BY_NAME[metric_name]

    metric = metric_class()

    return metric


def backfill_metric(metric_name: str):
    metric_names = _METRICS_BY_NAME.keys() if metric_name == "all" else [metric_name]

    for metric_name_ in metric_names:
        metric = _get_metric(metric_name_)
        metric.backfill()


@main.command("list", short_help="List metric points")
@common_options
@click.argument("metric_name", type=click.STRING)
@click.argument("scope_id", type=click.STRING)
def _list_metric(env: str, verbose: bool, metric_name: str, scope_id: str):
    _apply_common_options(env, verbose)
    list_metric(metric_name, scope_id)


def list_metric(metric_name: str, scope_id: str):
    metric = _get_metric(metric_name)

    plugin_points = metric.get_metrics(scope_id)
    for plugin_path, points in plugin_points.items():
        points = list(points)
        logging.info("%s points in %s", len(points), plugin_path)
        for point in points:
            print(point)


@main.command("clear", short_help="Clear metric points")
@common_options
@click.argument("metric_name", type=click.STRING)
@click.option("--scope-id", type=click.STRING)
def _clear_metric(
    env: str, verbose: bool, metric_name: str, scope_id: Optional[str] = None
):
    _apply_common_options(env, verbose)
    clear_metric(metric_name, scope_id)


def clear_metric(metric_name: str, scope_id: Optional[str] = None):
    metric = _get_metric(metric_name)
    metric.clear(scope_id)


@main.command("aggregate", short_help="Clear metric points")
@common_options
@click.argument("metric_name", type=click.STRING)
@click.option("--calculator_path", type=click.STRING)
@click.option("--root", is_flag=True)
@click.option("--group-by", type=str, multiple=True)
def _aggregate_metric(
    env: str,
    verbose: bool,
    metric_name: str,
    calculator_path: Optional[str] = None,
    group_by: Optional[List[str]] = None,
    root: Optional[bool] = None,
):
    _apply_common_options(env, verbose)

    labels: MetricsLabels = {}
    if calculator_path is not None:
        labels["calculator_path"] = calculator_path

    if root is not None:
        labels["root"] = True

    group_by_: List[GroupBy] = []
    if group_by is not None:
        group_by_ = [GroupBy(gb) for gb in group_by]

    aggregate_metric(metric_name, labels, group_by_)


def aggregate_metric(
    metric_name: str,
    labels: MetricsLabels,
    group_by: List[GroupBy],
):
    metric = _get_metric(metric_name)
    aggregations = metric.aggregate(labels, group_by)

    for plugin_path, aggregated_metric in aggregations.items():
        print(f"Aggregation for plugin {plugin_path}:")

        for value in aggregated_metric.series:
            labels_str = ", ".join(
                [
                    f"{aggregated_metric.group_by_labels[i]}={value[1][i]}"
                    for i in range(len(value[1]))
                ]
            )
            print(f"\t{labels_str}\t{value[0]}")
    """
        if metric_name not in aggregated_metric:
            print(f"No metric named {metric_name} stored in {plugin_path}")


        for label, point in aggregated_metric[metric_name].points.items():
            print(f"{label}\t{point[0]} over {point[1]} points")

        print(
            f"Total:\t\t{aggregated_metric[metric_name].total} "
            f"over {aggregated_metric[metric_name].count} points"
        )
    """


if __name__ == "__main__":
    main()
