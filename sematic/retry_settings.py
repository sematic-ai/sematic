# Standard Library
from dataclasses import dataclass, field
from typing import Tuple, Type

# Sematic
from sematic.utils.exceptions import ExceptionMetadata


@dataclass
class RetrySettings:
    exceptions: Tuple[Type[Exception]]
    times: int
    retry_count: int = field(default=0, init=False)

    def should_retry(self, exception_metadata: ExceptionMetadata) -> bool:
        if not self._matches_exceptions(exception_metadata):
            return False

        return self.retry_count < self.times

    def _matches_exceptions(self, exception_metadata: ExceptionMetadata) -> bool:
        return any(
            exception_type.__name__ == exception_metadata.name
            and exception_type.__module__ == exception_metadata.module
            for exception_type in self.exceptions
        )
