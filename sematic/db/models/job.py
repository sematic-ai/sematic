# Standard Library
import datetime
from dataclasses import asdict
from typing import Any, Dict, List, Sequence, Tuple, Union

# Third-party
from sqlalchemy import Column, types

# Sematic
from sematic.db.models.base import Base
from sematic.db.models.mixins.json_encodable_mixin import JSONEncodableMixin
from sematic.scheduling.job_details import (
    JobDetails,
    JobKindString,
    JobStatus,
    KubernetesJobStateString,
)
from sematic.types.types.dataclass import fromdict
from sematic.utils.exceptions import IllegalStateTransitionError


class Job(Base, JSONEncodableMixin):
    """Represents a K8s job managed by Sematic.

    This holds high-level metadata about the job, as well as its status history.
    The metadata here is primarily useful to the rest of Sematic. It contains a
    detail_serialization which can contain lots of information about the Kubernetes
    job & related pod(s).

    Attributes
    ----------
    name:
        The k8s name of the job. Used instead of an 'id' field because
        K8s identifies jobs by namespace and name.
    namespace:
        The k8s namespace of the job. In conjunction with name, forms
        the unique id for the job.
    run_id:
        The id of the run the job is associated with.
    last_updated_epoch_seconds:
        The time the job status was last synced with Kubernetes. Pulled from
        the most recent status to aid in queries.
    state:
        The simple state of the job. Pulled from the most recent status to
        aid in queries.
    kind:
        Whether the job is for executing a run or a resolution.
    message:
        The human-readable message for the latest status. Pulled from
        the most recent status to aid in queries.
    detail_serialization:
        A json-encoded serialization of detailed state information for the job
    status_history_serialization:
        A list of json-encoded serializations of job statuses. Statuses are in
        reverse-chronological order (most recent first).
    created_at:
        The time the DB record for the job was created
    updated_at:
        The time the DB record for the job was last updated
    """

    __tablename__ = "jobs"

    name: str = Column(types.String(), primary_key=True)
    namespace: str = Column(types.String(), primary_key=True)
    run_id: str = Column(types.String(), nullable=False)
    last_updated_epoch_seconds: float = Column(types.Float(), nullable=False)
    state: KubernetesJobStateString = Column(types.String(), nullable=False)
    kind: JobKindString = Column(types.String(), nullable=False)
    message: str = Column(types.String(), nullable=False)
    detail_serialization: Dict[str, Any] = Column(  # type: ignore
        types.JSON(), nullable=False
    )
    status_history_serialization: List[Dict[str, Union[str, float]]] = Column(
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

    def get_details(self) -> JobDetails:
        return fromdict(JobDetails, self.detail_serialization)

    def set_details(self, details: JobDetails) -> None:
        self.detail_serialization = asdict(details)

    details = property(get_details, set_details)

    def update_status(self, status: JobStatus):
        history = self.status_history
        prior_status = history[0]
        if prior_status.last_updated_epoch_seconds > status.last_updated_epoch_seconds:
            raise IllegalStateTransitionError(
                f"Tried to update status from {prior_status} to {status}, "
                f"but the latter was older"
            )
        if status.is_active() and not prior_status.is_active():
            raise IllegalStateTransitionError(
                f"Tried to update status from {prior_status.state} to {status.state}, "
                f"but the former is a terminal status"
            )

        self.last_updated_epoch_seconds = status.last_updated_epoch_seconds
        self.state = status.state
        self.message = status.message

        if prior_status != status:
            updated_history = list(history)
            updated_history.insert(0, status)
            self._set_status_history(updated_history)

    def get_status_history(self) -> Tuple[JobStatus, ...]:
        return tuple(
            fromdict(JobStatus, status) for status in self.status_history_serialization
        )

    def _set_status_history(self, status_history: Sequence[JobStatus]):
        self.status_history_serialization = [
            asdict(status) for status in status_history
        ]

    # don't expose setter; we want this to be read-only for clients. update_status
    # should be used to update status_history.
    status_history = property(get_status_history)

    def get_latest_status(self) -> JobStatus:
        """Get the most recent job status."""
        return JobStatus(
            state=self.state,
            message=self.message,
            last_updated_epoch_seconds=self.last_updated_epoch_seconds,
        )

    latest_status = property(get_latest_status)

    def __repr__(self) -> str:
        key_value_strings = [
            f"{field}={getattr(self, field)}"
            for field in (
                "name",
                "run_id",
                "state",
            )
        ]

        fields = ", ".join(key_value_strings)
        return f"Job({fields}, ...)"

    def identifier(self) -> str:
        """Get a single string uniquely identifying the job."""
        return f"{self.namespace}/{self.name}"
