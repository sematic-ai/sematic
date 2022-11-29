# Standard Library
from typing import Any

# Third-party
import matplotlib.figure  # type: ignore
from mpld3 import fig_to_dict

# Sematic
from sematic.types.registry import register_to_json_encodable_summary


@register_to_json_encodable_summary(matplotlib.figure.Figure)
def _mpl_figure_summary(value: matplotlib.figure.Figure, _) -> Any:
    # Without setting this DPI to 70 (default 100), the fonts on the
    # plot would be too small to see.
    value.set_dpi(70)
    fig_dict = fig_to_dict(value)
    return {"mpld3": fig_dict}
