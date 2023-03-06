# Standard Library
import numbers
from typing import Optional

# Sematic
import sematic.api_client as api_client
from sematic.db.models.metric import Metric, MetricScope
from sematic.future_context import NotInSematicFuncError, context


def post_pipeline_metric(
    name: str, value: numbers.Real, label: Optional[str] = None
) -> None:
    _post_metric(
        name=name,
        value=value,
        scope=MetricScope.PIPELINE,
        label=label,
    )


def post_run_metric(
    name: str, value: numbers.Real, label: Optional[str] = None
) -> None:
    _post_metric(
        name=name,
        value=value,
        scope=MetricScope.RUN,
        label=label,
    )


LABEL_ANNOTATION = "label"


def _post_metric(
    name: str,
    value: numbers.Real,
    scope: MetricScope,
    label: Optional[str] = None,
) -> None:
    try:
        current_context = context()
    except NotInSematicFuncError:
        raise NotInSematicFuncError(
            "Metrics can only be posted within Sematic functions."
        )

    if not isinstance(name, str) or len(name) == 0:
        raise ValueError("name cannot be empty")

    if not isinstance(value, numbers.Real):
        raise ValueError("value must be a real scalar")

    annotations = {}
    if label is not None:
        annotations[LABEL_ANNOTATION] = label

    metric = Metric(
        name=name,
        value=float(value),
        run_id=current_context.run_id,
        root_id=current_context.root_id,
        scope=scope.value,
        annotations=annotations,
    )

    api_client.save_metric(metric)
