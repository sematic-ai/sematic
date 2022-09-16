# Standard Library
from typing import Sequence, Tuple

# Sematic
from sematic.scheduling.external_job import ExternalJob
from sematic.types.serialization import (
    value_from_json_encodable,
    value_to_json_encodable,
)

# import dataclass to ensure dataclass serialization is registered
from sematic.types.types import dataclass  # noqa: F401


class HasExternalJobsMixin:
    """Mixin for ORM objects that have associated external compute jobs"""

    @property
    def external_jobs(self) -> Tuple[ExternalJob, ...]:
        """Representations of the external compute jobs used for the run."""
        encodables = self.external_jobs_json
        encodables = encodables if encodables is not None else []
        return tuple(value_from_json_encodable(job, ExternalJob) for job in encodables)

    @external_jobs.setter
    def external_jobs(self, jobs: Sequence[ExternalJob]):
        self.external_jobs_json = [
            value_to_json_encodable(job, ExternalJob) for job in jobs
        ]
