# Standard Library
import io
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

# Third-party
import boto3
import cloudpickle
from pytorch_lightning.plugins.io.checkpoint_plugin import CheckpointIO

# Sematic
from sematic.types.types.aws.s3 import S3Location
from sematic.utils.retry import retry


logger = logging.getLogger(__name__)


class SematicCheckpointIO(CheckpointIO):
    """Example checkpointer for usage with PyTorch Lightning & S3 storage.

    You can use the built-in PyTorch Lightning checkpointer with S3 (AWS),
    GCS (Google Cloud), or ADL (Azure) provided that you add extra dependencies.
    See Lightning Documentation:
    https://pytorch-lightning.readthedocs.io/en/stable/common/checkpointing_advanced.html
    """

    def __init__(self, *args, s3_location: S3Location = None, **kwargs) -> None:
        if s3_location is None:
            raise ValueError("Missing required argument 's3_location'")
        self._s3_location = s3_location
        super().__init__(*args, **kwargs)

    def save_checkpoint(
        self,
        checkpoint: Any,
        path: str,
        storage_options: Optional[Dict[str, Any]] = None,
    ):
        as_bytes = cloudpickle.dumps(checkpoint)
        s3_client = boto3.client("s3")
        key = (self._s3_location / path).location
        with io.BytesIO(as_bytes) as file_obj:
            s3_client.upload_fileobj(file_obj, self._s3_location.bucket.name, key)

    @retry(tries=3, delay=5)
    def load_checkpoint(
        self, path: str, storage_options: Optional[Dict[str, Any]] = None
    ) -> Any:
        file_obj = io.BytesIO()
        s3_client = boto3.client("s3")
        key = (self._s3_location / path).location
        logger.info("Loading checkpoint from %s", (self._s3_location / path).to_uri())
        s3_client.download_fileobj(self._s3_location.bucket.name, key, file_obj)
        return cloudpickle.loads(file_obj.getvalue())

    def remove_checkpoint(self, path: str) -> None:
        logger.warning(
            "Cannot remove checkpoints once "
            "they have been written. Ignoring removal of: %s",
            path,
        )

    def from_path(self, path: str) -> "Checkpoint":
        return Checkpoint(
            location=self._s3_location / path,
            prefix=self._s3_location,
        )


@dataclass
class Checkpoint:
    """Sematic representation of the Checkpoint.

    Attributes
    ----------
    location: The full location of the checkpoint
    prefix: The prefix the checkpointer was using when the checkpoint was created
    """

    location: S3Location
    prefix: S3Location

    @property
    def path(self) -> str:
        return self.location.location.replace(f"{self.prefix.location}/", "")
