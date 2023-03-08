# Standard Library
import datetime
from typing import Any, Dict, Tuple, Union

# Third-party
from sqlalchemy import Column, types
from sqlalchemy.orm import validates

# Sematic
from sematic.db.models.base import Base
from sematic.db.models.mixins.json_encodable_mixin import JSONEncodableMixin
from sematic.scheduling.external_job import ExternalJob, JobStatus, JobType
from sematic.types.serialization import (
    value_from_json_encodable,
    value_to_json_encodable,
)
from sematic.utils.exceptions import IllegalStateTransitionError


class Job(Base, JSONEncodableMixin):
    """A DB record for an ExternalJob (dataclass) and its history.

    Attributes
    ----------
    id:
        The unique id of the external resource
    source_run_id:
        The id of the run this job is associated with
    state_name:
        The name of the state this job is in
    status_message:
        A human-readable status message about the job's most recent state.
    job_type:
        The job type (ex: worker/driver) of this job.
    value_serialization:
        The Sematic serialization of the full external job. This may be more
        "volatile" over time relative to overall status information. Thus its
        contents are not extracted into individual fields.
    status_history_serializations:
        The Sematic serialization of the job's JobStatus objects over time. Any
        time the JobStatus object changes in such a way as to make the instances
        compare as not equal, a new entry will be added to this list.
        Element 0 is the most recent, element N the oldest.
    last_updated_epoch_seconds:
        The time that the job was last updated against the k8s job
        it represnets, expressed as epoch seconds. Ex: the last time k8s was
        queried for whether the job was alive. This differs from updated_at
        in that it relates to the updates against the external resources, while
        updated_at relates to updates of the DB record. It is in epoch seconds
        rather than as a datetime object because it will primarily be used in
        arithmetic operations with time (ex: comparing which value is more recent,
        amount of elapsed time since last update) rather than for human-readability
        of absolute time.
    created_at:
        The time this record was created in the DB.
    updated_at:
        The time this record was last updated in the DB. See documentation in
        last_updated_epoch_seconds for how this relates to that field.
    """

    # Q: Why duplicate data that's already in the json of
    # status_history_serializations and value_serialization as columns?
    # A: For two reasons:
    #    1. It gives us freedom to refactor the dataclass for
    #    JobStatus/ExternalJob/KubernetesExternalJob later to move fields around,
    #    while allowing the database columns to stay stable.
    #    2. It allows for more efficient queries on the explicit columns rather than
    #    requiring json traversal.

    __tablename__ = "jobs"

    id: str = Column(types.String(), primary_key=True)
    source_run_id: str = Column(  # type: ignore
        types.String(),
        nullable=False,
    )
    state_name: str = Column(  # type: ignore
        types.String(),
        nullable=False,
    )

    # Why do we need both state_name and is_active? The former is fairly
    # free-form and subject to change. The latter should be a stable way
    # to determine whether the job is in a terminal state or not, and
    # whether it is expected to change.
    is_active: int = Column(
        types.Integer, nullable=False  # sqlite doesn't support bool
    )
    status_message: str = Column(types.String(), nullable=False)
    job_type: JobType = Column(  # type: ignore
        types.Enum(JobType),
        nullable=False,
    )
    last_updated_epoch_seconds: float = Column(types.Float(), nullable=False)
    value_serialization: Dict[str, Any] = Column(types.JSON(), nullable=False)
    status_history_serializations: Tuple[Dict[str, Any], ...] = Column(  # type: ignore
        types.JSON(), nullable=False
    )
    created_at: datetime.datetime = Column(
        types.DateTime(), nullable=False, default=datetime.datetime.utcnow
    )
    updated_at: datetime.datetime = Column(
        types.DateTime(),
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    @validates("job_type")
    def validate_job_type(self, key: Any, job_type: Union[str, JobType]) -> JobType:
        if isinstance(job_type, str):
            return JobType[job_type]
        elif isinstance(job_type, JobType):
            return job_type
        raise ValueError(f"Cannot make a JobType from {job_type}")

    @classmethod
    def from_job(cls, job: ExternalJob, run_id: str) -> "Job":
        if not isinstance(job, ExternalJob):
            raise ValueError(
                f"resource must be an instance of a subclass of "
                f"ExternalJob. Was: {job} of type "
                f"'{type(job)}'"
            )
        value_serialization = value_to_json_encodable(job, type(job))
        status = job.get_status()
        status_serialization = value_to_json_encodable(status, type(status))

        return Job(
            id=job.external_job_id,
            source_run_id=run_id,
            state_name=status.state_name,
            is_active=int(job.is_active()),
            status_message=status.description,
            job_type=job.job_type,
            last_updated_epoch_seconds=status.last_update_epoch_time,
            value_serialization=value_serialization,
            status_history_serializations=(status_serialization,),
        )

    def get_job(self) -> ExternalJob:
        return value_from_json_encodable(self.value_serialization, ExternalJob)

    def set_job(self, job: ExternalJob) -> None:
        if not isinstance(job, ExternalJob):
            raise ValueError(f"job must be a subclass of ExternalJob. Was: {type(job)}")

        if job.external_job_id != self.id:
            raise ValueError(
                f"Job can only be updated by another job with the same id. "
                f"Original id: {self.id}, new id: {job.external_job_id}"
            )

        if job.job_type != self.job_type:
            raise ValueError(
                f"Job cannot change job type from {self.job_type} to {job.job_type}"
            )

        if job.is_active() and not self.is_active:
            raise IllegalStateTransitionError(
                f"Job was inactive, can't be made active again. "
                f"Former state: {self.state_name}, new state: "
                f"{job.get_status().state_name}"
            )

        serialization = value_to_json_encodable(job, type(job))
        most_recent_status = None
        current_status = job.get_status()
        status_serialization = value_to_json_encodable(current_status, JobStatus)
        if len(self.status_history_serializations) > 0:
            most_recent_status = value_from_json_encodable(
                self.status_history_serializations[0], JobStatus
            )
            if (
                most_recent_status.last_update_epoch_time
                > current_status.last_update_epoch_time
            ):
                raise IllegalStateTransitionError(
                    "Cannot append status to history, a more recent "
                    "update is already available."
                )
        if current_status != most_recent_status:
            history = list(self.status_history_serializations)
            history.insert(0, status_serialization)
            self.status_history_serializations = tuple(history)

        self.state_name = current_status.state_name
        self.status_message = current_status.description
        self.last_updated_epoch_seconds = current_status.last_update_epoch_time
        self.is_active = int(job.is_active())

        self.value_serialization = serialization

    job = property(get_job, set_job)

    @property
    def status_history(self) -> Tuple[JobStatus, ...]:
        return tuple(
            value_from_json_encodable(status, JobStatus)
            for status in self.status_history_serializations
        )

    def __repr__(self) -> str:
        key_value_strings = [
            f"{field}={getattr(self, field)}"
            for field in (
                "id",
                "state_name",
                "source_run_id",
                "status_message",
            )
        ]

        fields = ", ".join(key_value_strings)
        return f"Job({fields}, ...)"
