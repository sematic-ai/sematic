# Standard Library
import uuid
from dataclasses import dataclass

# Third-party
import magic

# Sematic
from sematic.types.registry import SummaryOutput, register_to_json_encodable_summary


@dataclass
class Image:
    bytes: bytes

    @classmethod
    def from_file(cls, file_path: str) -> "Image":
        with open(file_path, "rb") as file:
            return Image(bytes=file.read())


@register_to_json_encodable_summary(Image)
def _image_to_summary(value: Image, _) -> SummaryOutput:
    blob_id = uuid.uuid4().hex
    mime_type = magic.from_buffer(value.bytes, mime=True)

    summary = {"mime_type": mime_type, "bytes": {"blob": blob_id}}

    return summary, {blob_id: value.bytes}
