# Standard Library
import hashlib
import logging
import platform
from dataclasses import dataclass

# Sematic
from sematic.types.registry import SummaryOutput, register_to_json_encodable_summary

logger = logging.getLogger(__name__)


def _log_magic_import_error(e: Exception, fatal: bool = False) -> None:
    """
    Attempts to import the `magic` module, and either warns or errors and raises based on
    the value of the parameter.

    This is meant to allow execution until the `Image` type is actually used, in order to
    not burden users with dependencies they don't actually require.
    """

    template = (
        "Sematic requires the `libmagic` package in order to work with the `Image` type. "
        "Please install it{os_message}"
    )
    mapping = {
        "Darwin": " with `brew install libmagic`, or with `port install file`.",
        "Linux": (
            " with `sudo apt-get install libmagic1`, "
            "or with `sudo yum install file-devel`."
        ),
    }
    error_message = template.format(os_message=mapping.get(platform.system(), "."))

    if fatal:
        raise ImportError(error_message) from e

    logger.warning(error_message)


magic_import_error = None
try:
    # Third-party
    import magic  # type: ignore

except ImportError as e:
    _log_magic_import_error(e, fatal=False)
    magic_import_error = e


@dataclass
class Image:
    """
    A simple type to display images in the Dashboard.
    """

    bytes: bytes

    @classmethod
    def from_file(cls, file_path: str) -> "Image":
        with open(file_path, "rb") as file:
            return Image(bytes=file.read())


@register_to_json_encodable_summary(Image)
def image_to_summary(value: Image, _) -> SummaryOutput:

    if magic_import_error is not None:
        _log_magic_import_error(magic_import_error, fatal=True)

    blob_id = hashlib.sha1(value.bytes).hexdigest()
    mime_type = magic.from_buffer(value.bytes, mime=True)

    summary = {"mime_type": mime_type, "bytes": {"blob": blob_id}}

    return summary, {blob_id: value.bytes}
