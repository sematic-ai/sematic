# Standard Library
import base64
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Tuple

# Sematic
from sematic.types.registry import register_to_json_encodable_summary


@dataclass
class Image:
    bytes: bytes

    @classmethod
    def from_file(cls, file_path: str) -> "Image":
        with open(file_path, "rb") as file:
            return Image(bytes=file.read())


@register_to_json_encodable_summary(Image)
def _image_to_summary(value: Image, _) -> Tuple[Any, Dict[str, bytes]]:
    encoded_string = base64.b64encode(value.bytes)
    blob_id = uuid.uuid4().hex
    return {"bytes": {"blob": blob_id}}, {blob_id: encoded_string}
