# Standard Library
import time
from dataclasses import dataclass, field
from typing import List, Literal, Optional

# Sematic
from sematic.utils.exceptions import ExceptionMetadata, KubernetesError

# TODO: remove ExternalJob and KubernetesExternalJob once they are replaced by this & Job

# ordered from highest to lowest precedence
# to be interpreted as: pods with phases earlier in the list are newer
# interpreted from the list from this resource:
# https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-conditions
# no official documentation exists regarding "Unknown"'s state transitions
POD_PHASE_PRECEDENCE = ["Unknown", "Pending", "Running", "Succeeded", "Failed"]


# This is not an Enum because dataclasses.asdict doesn't produce
# a json-serializable result for enums.
class KubernetesJobState:
    """Simple strings describing the K8s job state.

    Though it is meant to be associated with the *job* it draws
    from details relating to the *pod*, as the latter is more
    information-rich. A "Job" may show up as active for both a pending
    and a running pod, for example.

    Drawn from the docs for pod lifecycle:
    https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/

    Some additional states are added to represent the extra tracking
    Sematic is performing. Extra states not covered in pod lifecycle
    include:
    - Requested
    - Deleted
    - Restarting
    - Terminated

    Attributes
    ----------
    Requested:
        Sematic has requested the job, but Kubernetes has not yet assigned a status
        to it.
    Pending:
        The pod for the job is in the "Pending" phase.
    Running:
        The pod for the job is in the "Running" phase.
    Restarting:
        The job is in an intermediate state where one pod is being removed
        while another is being created.
    Succeeded:
        The job has at least one pod which has exited with a 0 status.
    Failed:
        The job ended with no pods in a succeeded state.
    Deleted:
        The job once existed, but does no longer.
    """

    def __init__(self) -> None:
        raise RuntimeError(
            "This is meant to emulate an Enum and not to be instantiated directly"
        )

    Requested: "KubernetesJobStateString" = "Requested"
    Pending: "KubernetesJobStateString" = "Pending"
    Running: "KubernetesJobStateString" = "Running"
    Restarting: "KubernetesJobStateString" = "Restarting"
    Succeeded: "KubernetesJobStateString" = "Succeeded"
    Failed: "KubernetesJobStateString" = "Failed"
    Deleted: "KubernetesJobStateString" = "Deleted"

    @classmethod
    def is_active(cls, state) -> bool:
        return state in _ACTIVE_STATES


_ACTIVE_STATES = {
    KubernetesJobState.Requested,
    KubernetesJobState.Pending,
    KubernetesJobState.Running,
    KubernetesJobState.Restarting,
}

KubernetesJobStateString = Literal[
    "Requested",
    "Pending",
    "Running",
    "Restarting",
    "Succeeded",
    "Failed",
    "Deleted",
]


class JobKind:
    def __init__(self) -> None:
        raise RuntimeError("This is meant to emulate an enum, not be instantiated.")

    resolver: "JobKindString" = "resolver"
    run: "JobKindString" = "run"


JobKindString = Literal[
    "resolver",
    "run",
]


@dataclass
class PodSummary:
    """Summary of an individual pod associated with a job."""

    # Unique name of the pod assigned by K8s
    pod_name: str

    # number of times the container within the pod has
    # been restarted. Is NOT the number of pods that
    # has been associated with the associated job.
    container_restart_count: Optional[int] = None

    # Current phase in the lifecycle of the pod.
    phase: Optional[str] = None

    # Human readable message associated with the most recent
    # "relevant" condition of the job. Relevancy is based on
    # condition kind and True/False value.
    condition_message: Optional[str] = None

    # Human readable reason why the pod is unschedulable
    # (assuming the pod is currently unschedulable). Note that
    # just because a pod is *currently* unschedulable doesn't mean
    # that autoscaling or workload drops won't make it schedulable at
    # some point.
    unschedulable_message: Optional[str] = None

    # Human readable message about the state of the container
    # associated with the pod.
    container_condition_message: Optional[str] = None

    # Exit code of the container, assuming the container has exited and
    # the exit code can be identified.
    container_exit_code: Optional[int] = None

    # Epoch time that Kubernetes started the pod.
    start_time_epoch_seconds: Optional[float] = None

    # Name of the node the pod is running on, if it
    # has been scheduled to a node.
    node_name: Optional[str] = None

    # Indicator of whether the pod has shown some abnormality
    # that shows that Sematic should move the current run to
    # a terminal state (or retry it).
    has_infra_failure: bool = False

    def string_summary(self, use_newlines=False) -> str:
        if use_newlines:
            return (
                f"{self.pod_name} is in phase '{self.phase}'\n"
                f"{self.condition_message}\n"
                f"{self.container_condition_message}"
            )
        else:
            return (
                f"{self.pod_name}[in phase '{self.phase}']"
                f"[{self.condition_message}]"
                f"[{self.container_condition_message}]"
            )


@dataclass(frozen=True)
class JobStatus:
    """A simple status object describing the state of the job.

    Attributes
    ----------
    state:
        This should be a one-word descriptor of the state of the job. Ex:
        "Pending", "Running", etc.
    message:
        This should be a human-readable description of the state of the job,
        no more than a couple short sentences pointing out any unique details
        about the state of the job.
    last_updated_epoch_seconds:
        The time this status object was generated, as epoch seconds.
    """

    state: KubernetesJobStateString
    message: str
    last_updated_epoch_seconds: float = field(compare=False)

    def is_active(self) -> bool:
        """Indicates whether the job is still active.

        Active in this context means whether or not it may still evolve
        the run's future. Note that this method is based only on the
        in-memory ExternalJob and doesn't reach out to the external job source.

        Returns
        -------
        True if the job is still active, False otherwise.
        """
        return KubernetesJobState.is_active(self.state)


@dataclass
class JobDetails:
    """Detailed information about the state of the job.

    For relevant K8s docs on job status, see:
        github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1JobStatus.md
    and: https://kubernetes.io/docs/concepts/workloads/controllers/job/

    Explanation of k8s status conditions:
    https://maelvls.dev/kubernetes-conditions/
    """

    # What Sematic retry number is this job associated with?
    try_number: int

    # pending_or_running_pod_count is the "active" property.
    pending_or_running_pod_count: int = 0

    # count of jobs that have finished successfully
    succeeded_pod_count: int = 0

    # has the Kubernetes job object been observed on Kubernetes?
    has_started: bool = False

    # True so long as the job is detectable in K8s
    still_exists: bool = True

    # epoch seconds that the job was created by Sematic at
    start_time: float = field(default_factory=time.time)

    # Set to True if some abonormality is detected that indicates the
    # Sematic run should be forced to a terminal state or retried.
    has_infra_failure: bool = False

    # List of summaries of pods currently associated with a job. 99%
    # of the time should contain only one pod. But there might be
    # transient moments where one pod is being terminated and another one
    # started simultaneously.
    current_pods: List[PodSummary] = field(default_factory=list)

    # represents the name the pod had before the latest refresh happened.
    # None means the prior refresh had no pod name (which is true to
    # begin with). It may match latest_pod_name if the pod name hasn't
    # changed between refreshes. Used to detect when K8s replaces the
    # job's pod.
    previous_pod_name: Optional[str] = None

    # represents the node the pod was assigned to before the latest
    # refresh happened. None means the prior refresh had no node name
    # (which is true until the pod is scheduled). It may match
    # latest_pod_name if the pod name hasn't changed between refreshes.
    # Used to detect when K8s replaces the job's pod.
    previous_node_name: Optional[str] = None

    def latest_pod_summary(self) -> Optional[PodSummary]:
        if len(self.current_pods) == 0:
            return None

        def order_key(summary):
            """Order pods first by phase, then start time.
            It's important to not just rely on start time because pending
            pods don't have one.
            """
            phase_key = -1
            if summary.phase is not None:
                phase_key = POD_PHASE_PRECEDENCE.index(summary.phase)
            start_time_key = summary.start_time_epoch_seconds or 0
            return (phase_key, start_time_key)

        latest = max(self.current_pods, key=order_key)
        return latest

    def latest_pod_name(self) -> Optional[str]:
        summary = self.latest_pod_summary()
        if summary is None:
            return None
        return summary.pod_name

    def latest_node_name(self) -> Optional[str]:
        summary = self.latest_pod_summary()
        if summary is None:
            return None
        return summary.node_name

    def get_exception_metadata(self) -> Optional[ExceptionMetadata]:
        if not self.has_infra_failure:
            return None

        latest_pod_summary = self.latest_pod_summary()
        if latest_pod_summary is None:
            message = "No pods could be found."
        else:
            message = latest_pod_summary.string_summary(use_newlines=True)

        return ExceptionMetadata(
            repr=message,
            name=KubernetesError.__name__,
            module=KubernetesError.__module__,
            ancestors=ExceptionMetadata.ancestors_from_exception(KubernetesError),
        )
