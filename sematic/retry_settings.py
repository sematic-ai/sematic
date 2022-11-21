# Standard Library
import logging
from dataclasses import dataclass, field
from typing import Optional, Tuple, Type

# Sematic
from sematic.utils.exceptions import ExceptionMetadata

logger = logging.getLogger(__name__)


@dataclass
class RetrySettings:
    """
    Configuration object to pass to `@sematic.func` to activate retries.

    Parameters
    ----------
    exceptions: Tuple[Type[Exception]]
        A tuple of exception types to retry for.

    retries: int
        How may times to retry.
    """

    exceptions: Tuple[Type[Exception]]
    retries: int
    retry_count: int = field(default=0, init=False)

    def __post_init__(self):
        if not isinstance(self.exceptions, (tuple, list, set)):
            raise ValueError(f"exceptions should be a tuple, got {self.exceptions}")

    def should_retry(
        self, *exception_metadata_tuple: Optional[ExceptionMetadata]
    ) -> bool:
        """
        Should the given exceptions trigger a retry?

        If this is called with no effective parameters or only with None values, it means
        we are in an abnormal situation in which a future failed with no known cause.

        Parameters
        ----------
        exception_metadata_tuple: Tuple[Optional[ExceptionMetadata]]
            Metadata describing a series of exceptions that have affected execution.
        """
        filtered_list = [e for e in exception_metadata_tuple if e is not None]
        if len(filtered_list) == 0:
            logger.warning(
                "`should_retry` called with no effective exception metadata! "
                "Unknown failure situation!"
            )
            return False

        if not any(map(self._matches_exceptions, filtered_list)):
            return False

        return self.retry_count < self.retries

    def _matches_exceptions(self, exception_metadata: ExceptionMetadata) -> bool:
        return any(
            exception_metadata.is_instance_of(exception_type)
            for exception_type in self.exceptions
        )
