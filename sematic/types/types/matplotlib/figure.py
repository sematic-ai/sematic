# Standard Library
from io import BytesIO

# Third-party
import matplotlib.figure  # type: ignore

# Sematic
from sematic.types.registry import SummaryOutput, register_to_json_encodable_summary
from sematic.types.types.image import Image, image_to_summary


@register_to_json_encodable_summary(matplotlib.figure.Figure)
def _mpl_figure_summary(value: matplotlib.figure.Figure, _) -> SummaryOutput:
    file_obj = BytesIO()
    value.savefig(file_obj)
    file_obj.flush()
    file_obj.seek(0)
    image = Image(bytes=file_obj.read())

    return image_to_summary(image, Image)
