# Standard Library
import io
from typing import Any

# Third-party
import matplotlib.figure  # type: ignore

# Sematic
from sematic.types.registry import register_to_json_encodable_summary
from sematic.types.serialization import binary_to_string


@register_to_json_encodable_summary(matplotlib.figure.Figure)
def _mpl_to_json_summary(value: matplotlib.figure.Figure, _) -> Any:
    # Without setting this DPI to 70 (default 100), the fonts on the
    # plot would be too small to see.
    value.set_dpi(70)

    f = io.BytesIO()
    value.savefig(f)
    image_base64 = binary_to_string(f.getvalue())
    f.close()
    return dict(
        image_base64=image_base64,
    )


"""
@register_to_json_encodable(matplotlib.figure.Figure)
def _mpl_to_json_encodable(value: matplotlib.figure.Figure, _) -> Any:
    figure_bytes = binary_to_string(cloudpickle.dumps(value))

    # Without setting this DPI to 70 (default 100), the fonts on the
    # plot would be too small to see.
    value.set_dpi(70)

    f = io.BytesIO()
    value.savefig(f)
    image_bytes = binary_to_string(f.getvalue())

    return dict(
        figure_bytes=figure_bytes,
        image_bytes=image_bytes,
        metadata=dict(width=value.get_figwidth(), height=value.get_figheight()),
    )


@register_from_json_encodable(matplotlib.figure.Figure)
def _mpl_from_json_encodable(value: Dict[str, Any], _) -> matplotlib.figure.Figure:
    figure_bytes = value["figure_bytes"]

    return cloudpickle.loads(binary_from_string(figure_bytes))
"""
