# Standard Library
import enum
from dataclasses import dataclass

KUBERNETES_JOB_KIND = "k8s"


class JobType(enum.Enum):
    driver = "driver"
    worker = "worker"


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
        in-memory RunJob and doesn't reach out to the external job source.

        Returns
        -------
        True if the job is still active, False otherwise.
        """
        raise NotImplementedError("Subclasses of ExternalJob should define is_active")
