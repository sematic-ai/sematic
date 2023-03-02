import logging
from dataclasses import dataclass
import os
import io
import tempfile
import boto3
import botocore.exceptions
from sematic.utils.retry import retry
import cloudpickle
from pytorch_lightning.plugins.io.checkpoint_plugin import CheckpointIO

logger = logging.getLogger(__name__)

class SematicCheckpointIO(CheckpointIO):
    def __init__(self, *args, bucket=None, prefix=None, **kwargs) -> None:
        if bucket is None:
            raise ValueError("Missing required argument bucket")
        if prefix is None:
            raise ValueError("Missing required argument prefix")
        self._bucket = bucket
        self._prefix = prefix if not prefix.endswith("/") else prefix[-1]
        super().__init__(*args, **kwargs)

    def save_checkpoint(self, checkpoint, path, storage_options=None):
        as_bytes = cloudpickle.dumps(checkpoint)
        s3_client = boto3.client("s3")
        key = f"{self._prefix}/{path}"
        with io.BytesIO(as_bytes) as file_obj:
            s3_client.upload_fileobj(file_obj, self._bucket, key)

    @retry(tries=3, delay=5)
    def load_checkpoint(self, path, storage_options=None):
        file_obj = io.BytesIO()
        s3_client = boto3.client("s3")
        key = f"{self._prefix}/{path}"
        s3_client.download_fileobj(self._bucket, key, file_obj)        
        return cloudpickle.loads(file_obj.getvalue())

    def remove_checkpoint(self, path):
        logger.warning(
            f"Cannot remove checkpoints once "
            f"they have been written. Ignoring removal of: {path}"
        )
    
    def from_path(self, path):
        return Checkpoint(
            path=path,
            prefix=self._prefix,
            bucket=self._bucket,
        )


@dataclass
class Checkpoint:
    path: str
    source_run_id: str
