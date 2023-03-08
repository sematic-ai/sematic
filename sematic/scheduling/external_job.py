# Standard Library
import enum
import time
from dataclasses import dataclass, field
from typing import Optional

# Sematic
from sematic.utils.exceptions import ExceptionMetadata

KUBERNETES_JOB_KIND = "k8s"


class JobType(enum.Enum):
    driver = "driver"
    worker = "worker"


@dataclass
class JobStatus:
    """A simple status object describing the state of the job

    Attributes
    ----------
    state_name:
        This should be a one-word descriptor of the state of the job. Ex:
        "Pending", "Running", etc.
    description:
        This should be a human-readable description of the state of the job,
        no more than a couple short sentences pointing out any unique details
        about the state of the job.
    last_update_epoch_time:
        The time this status object was generated, as epoch seconds.
    """

    state_name: str
    description: str
    last_update_epoch_time: int = field(
        default_factory=lambda: int(time.time()), compare=False
    )


@dataclass
class ExternalJob:
    """A reference to a job on external compute that is executing a run.

    Parameters
    ----------
    kind:
        A string representing what kind of compute is being used for
        executing the external job. For now, this is always "k8s".
    try_number:
        An integer representing what trial number of the run this
        external job represents (until we implement run retries this
        will be 0).
    external_job_id:
        A string that can be used to look up the external job.
    """

    kind: str
    try_number: int
    external_job_id: str

    def is_active(self) -> bool:
        """Indicates whether the job is still active.

        Active in this context means whether or not it may still evolve
        the run's future. Note that this method is based only on the
        in-memory ExternalJob and doesn't reach out to the external job source.

        Returns
        -------
        True if the job is still active, False otherwise.
        """
        raise NotImplementedError("Subclasses of ExternalJob should define is_active")

    def get_exception_metadata(self) -> Optional[ExceptionMetadata]:
        """Returns an `ExceptionMetadata` object in case the job has experienced a
        failure.
        """
        return None

    def get_status(self) -> JobStatus:
        """Get a simple status describing the state of the job.

        Note that the returned status should be based on the in-memory
        fields of the ExternalJob, and should not reach out to the external
        job source.

        Returns
        -------
        A job status.
        """
        raise NotImplementedError("Subclasses of ExternalJob should define get_status")

    @property
    def job_type(self) -> JobType:
        """Get a JobType for the current job

        Returns
        -------
        A JobType.
        """
        raise NotImplementedError("Subclasses of ExternalJob should define job_type")
