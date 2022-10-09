# Standard Library
from dataclasses import dataclass, field
from typing import Tuple, Type

# Sematic
from sematic.utils.exceptions import ExceptionMetadata


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

    def should_retry(self, exception_metadata: ExceptionMetadata) -> bool:
        """
        Should the given exception trigger a retry?
        """
        if not self._matches_exceptions(exception_metadata):
            return False

        return self.retry_count < self.retries

    def _matches_exceptions(self, exception_metadata: ExceptionMetadata) -> bool:
        return any(
            exception_type.__name__ == exception_metadata.name
            and exception_type.__module__ == exception_metadata.module
            for exception_type in self.exceptions
        )
