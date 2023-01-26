# Standard Library
import io
from typing import Any

# Third-party
import PIL.Image

# Sematic
from sematic.types.registry import register_to_json_encodable_summary
from sematic.types.serialization import binary_to_string


@register_to_json_encodable_summary(PIL.Image.Image)
def _pil_image_to_json_summary(value: PIL.Image.Image, _) -> Any:
    f = io.BytesIO()

    width, height = value.size
    if width > 800:
        width, height = 800, int(800.0 / width * height)
        value = value.resize((width, height))

    value.save(f, format="png")

    image_base64 = binary_to_string(f.getvalue())

    f.close()

    return dict(
        image_base64=image_base64,
    )
