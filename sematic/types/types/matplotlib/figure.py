# Standard Library
from typing import Any

# Third-party
import matplotlib.figure  # type: ignore
from mpld3 import fig_to_dict

# Sematic
from sematic.types.registry import register_to_json_encodable_summary


@register_to_json_encodable_summary(matplotlib.figure.Figure)
def _mpl_figure_summary(value: matplotlib.figure.Figure, _) -> Any:
    fig_dict = fig_to_dict(value)
    return {"mpld3": fig_dict}
