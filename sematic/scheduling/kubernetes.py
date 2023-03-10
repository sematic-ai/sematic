# Standard Library
import logging
import pathlib
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, unique
from typing import Any, Dict, List, Optional, Tuple

# Third-party
import kubernetes
from kubernetes.client.exceptions import ApiException, OpenApiException
from kubernetes.client.models import (
    V1ContainerStatus,
    V1Job,
    V1Pod,
    V1PodCondition,
    V1Volume,
    V1VolumeMount,
)
from urllib3.exceptions import ConnectionError

# Sematic
from sematic.config.config import KUBERNETES_POD_NAME_ENV_VAR, ON_WORKER_ENV_VAR
from sematic.config.server_settings import ServerSettingsVar, get_server_setting
from sematic.config.settings import get_plugin_setting
from sematic.config.user_settings import UserSettingsVar
from sematic.container_images import CONTAINER_IMAGE_ENV_VAR
from sematic.plugins.storage.s3_storage import S3Storage, S3StorageSettingsVar
from sematic.resolvers.resource_requirements import (
    KUBERNETES_SECRET_NAME,
    KubernetesResourceRequirements,
    KubernetesSecretMount,
    ResourceRequirements,
)
from sematic.scheduling.external_job import (
    KUBERNETES_JOB_KIND,
    ExternalJob,
    JobStatus,
    JobType,
)
from sematic.utils.exceptions import ExceptionMetadata, KubernetesError
from sematic.utils.retry import retry

logger = logging.getLogger(__name__)
_kubeconfig_loaded = False

# ordered from highest to lowest precedence
# to be interpreted as: pods with phases earlier in the list are newer
# interpreted from the list from this resource:
# https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-conditions
# no official documentation exists regarding "Unknown"'s state transitions
POD_PHASE_PRECEDENCE = ["Unknown", "Pending", "Running", "Succeeded", "Failed"]
POD_FAILURE_PHASES = {"Failed", "Unknown"}
# ordered from highest to lowest precedence
# to be interpreted as: conditions earlier in the list are more recent
# interpreted from the list from this resource:
# https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-conditions
POD_CONDITION_PRECEDENCE = [
    "Ready",
    "ContainersReady",
    "Initialized",
    "PodHasNetwork",
    "PodScheduled",
]
RESOLUTION_RESOURCE_REQUIREMENTS = ResourceRequirements(
    kubernetes=KubernetesResourceRequirements(
        requests={"cpu": "500m", "memory": "2Gi"},
    )
)

DEFAULT_WORKER_SERVICE_ACCOUNT = "default"


@unique
class KubernetesJobCondition(Enum):
    Complete = "Complete"
    Failed = "Failed"


@unique
class KubernetesJobState(Enum):
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
    Pending:
    Running:
    Restarting:
    Succeeded:
    Failed:
        The job ended with no pods in a succeeded state.
    Deleted:
        The job once existed, but does no longer.
    """

    Requested = "Requested"
    Pending = "Pending"
    Running = "Running"
    Restarting = "Restarting"
    Succeeded = "Succeeded"
    Failed = "Failed"
    Deleted = "Deleted"

    def is_active(self) -> bool:
        return self in {
            KubernetesJobState.Requested,
            KubernetesJobState.Pending,
            KubernetesJobState.Running,
            KubernetesJobState.Restarting,
        }


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
    detected_infra_failure: bool = False

    def string_summary(self) -> str:
        return (
            f"{self.pod_name}[in phase '{self.phase}']"
            f"[{self.condition_message}]"
            f"[{self.container_condition_message}]"
        )


@dataclass
class KubernetesExternalJob(ExternalJob):
    """Summary of a Kubernetes Job object.

    There is a 1:1 mapping between a TRY of a Sematic run and a job.
    A job may have one or more pods associated with it throughout
    its lifetime. The common case is one pod, but pod failures, evictions,
    etc. may lead to multiple pods per job.
    """

    # See
    # github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1JobStatus.md
    # and: https://kubernetes.io/docs/concepts/workloads/controllers/job/
    # Explanation of k8s status conditions:
    # https://maelvls.dev/kubernetes-conditions/

    # TODO #271: deduplicate and rename these properties for ergonomics
    # this would require a python migration of the db

    # pending_or_running_pod_count is the "active" property.
    pending_or_running_pod_count: int

    # count of jobs that have finished successfully
    succeeded_pod_count: int

    # has the Kubernetes job object been observed on Kubernetes?
    has_started: bool

    # True so long as BOTH are true:
    # - the job is detectable in K8s
    # - has_started is True
    still_exists: bool

    # epoch seconds that the job was created by Sematic at
    start_time: Optional[float]

    # Most recent "relevant" condition of the most recent pod
    # for the run. Relevancy filters are based on certain job
    # condition types and True/False values. Can be None if no
    # pod or relevant condition exist.
    most_recent_condition: Optional[str]

    # Human readable message about the phase of the most
    # recent pod. Can be None if no pod can be found.
    most_recent_pod_phase_message: Optional[str]

    # Human readable message summarizing most_recent_condition
    most_recent_pod_condition_message: Optional[str]

    # Human readable message summarizing the most recent condition
    # of the container within the most recent pod. Can be None
    # if no pod/container exist.
    most_recent_container_condition_message: Optional[str]

    # Set to True if some abonormality is detected that indicates the
    # Sematic run should be forced to a terminal state or retried.
    has_infra_failure: Optional[bool]

    # List of summaries of pods currently associated with a job. 99%
    # of the time should contain only one pod. But there might be
    # transient moments where one pod is being terminated and another one
    # started simultaneously.
    current_pods: List[PodSummary] = field(default_factory=list)

    # represents the name the pod had before the latest refresh happened.
    # None means the prior refresh had no pod name (which is true to
    # begin with). It may match latest_pod_name if the pod name hasn't
    # changed between refreshes.
    previous_pod_name: Optional[str] = None

    # represents the name the node the pod had before the latest refresh happened.
    # None means the prior refresh had no node (which is true to
    # begin with). It may match latest_node_name if the pod's node hasn't
    # changed between refreshes.
    previous_node_name: Optional[str] = None

    # default value: need one so we're backwards compatible
    # with old serializations missing this field
    # why not time.time()?: that would imply the updates are
    # recent, when due to the fact that this is only missing for
    # old runs is a bad assumption. Better to treat them as
    # indefinitely old
    epoch_time_last_updated: float = field(default=0.0, compare=False, hash=False)

    @classmethod
    def new(
        cls, try_number: int, run_id: str, namespace: str, job_type: JobType
    ) -> "KubernetesExternalJob":
        """Get a job with an appropriate configuration for having just started."""
        return KubernetesExternalJob(
            kind=KUBERNETES_JOB_KIND,
            try_number=try_number,
            external_job_id=cls.make_external_job_id(run_id, namespace, job_type),
            pending_or_running_pod_count=1,
            succeeded_pod_count=0,
            has_started=False,
            still_exists=True,
            start_time=None,
            most_recent_condition=None,
            most_recent_pod_phase_message=None,
            most_recent_pod_condition_message=None,
            most_recent_container_condition_message=None,
            has_infra_failure=False,
            epoch_time_last_updated=time.time(),
        )

    @property
    def run_id(self) -> str:
        return self.kubernetes_job_name.split("-")[-2]

    @property
    def namespace(self) -> str:
        return self.external_job_id.split("/")[0]

    @property
    def job_type(self) -> JobType:
        return JobType[self.kubernetes_job_name.split("-")[1]]

    @property
    def kubernetes_job_name(self) -> str:
        return self.external_job_id.split("/")[-1]

    @classmethod
    def make_external_job_id(
        self, run_id: str, namespace: str, job_type: JobType
    ) -> str:
        job_name = "-".join(
            ("sematic", job_type.value, run_id, _unique_job_id_suffix())
        )
        return f"{namespace}/{job_name}"

    def is_active(self) -> bool:
        status = self.get_status()
        logger.info("Job %s status: %s", self.external_job_id, status)
        return KubernetesJobState[status.state_name].is_active()

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

    def get_status(self) -> JobStatus:
        """Get a simple status describing the state of the job.

        Note that the returned status should be based on the in-memory
        fields of the ExternalJob, and should not reach out to the external
        job source.

        Returns
        -------
        A job status.
        """
        # According to the docs:
        # github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1JobStatus.md
        # a job's "active" field holds the number of pending or running pods.
        # This should be a more reliable measure of whether the job is still
        # active than the number of succeeded or failed pods, as during pod
        # evictions (which don't stop the job completely, but do stop the pod),
        # a pod can briefly show up as failed even when another one is
        # going to be scheduled in its place.

        latest_summary = self.latest_pod_summary()
        if not self.has_started:
            description = "The job has been requested, but no pods are created yet."
            if self.try_number != 0:
                description += (
                    f"Sematic has retried the job, this is try "
                    f"number {self.try_number + 1}"
                )
            return JobStatus(
                state_name=KubernetesJobState.Requested.value,
                description=description,
                last_update_epoch_time=self.epoch_time_last_updated,
            )
        elif not self.still_exists:
            return JobStatus(
                state_name=KubernetesJobState.Deleted.value,
                description="The job no longer exists",
                last_update_epoch_time=self.epoch_time_last_updated,
            )
        elif self.most_recent_condition == KubernetesJobCondition.Complete.value:
            return JobStatus(
                state_name=KubernetesJobState.Succeeded.value,
                description="The job has completed successfully",
                last_update_epoch_time=self.epoch_time_last_updated,
            )
        elif self.most_recent_condition == KubernetesJobCondition.Failed.value or (
            latest_summary is not None and latest_summary.detected_infra_failure
        ):
            return self._get_job_failed_status(
                latest_summary=latest_summary,
                epoch_time_last_updated=self.epoch_time_last_updated,
            )
        elif self.succeeded_pod_count != 0:
            return JobStatus(
                state_name=KubernetesJobState.Succeeded.value,
                description=(
                    "The job has completed successfully, "
                    "but the final status on the pod was not set"
                ),
                last_update_epoch_time=self.epoch_time_last_updated,
            )
        elif self.pending_or_running_pod_count == 0:
            # I suppose this could happen if we catch the job in the brief
            # interval between when the job object is created and a pod
            # is requested for it. Should be *incredibly* rare though
            logger.warning("Unusual job state detected: %s", self)
            return JobStatus(
                state_name=KubernetesJobState.Pending.value,
                description=(
                    "No pods were considered succeeded, but none are pending/running."
                ),
                last_update_epoch_time=self.epoch_time_last_updated,
            )
        elif latest_summary is None:
            # *hopefully* should be impossible to reach here; it means the
            # job object says it has a pod, but Sematic was unable to identify
            # such a pod.
            logger.warning("Unusual job state detected: %s", self)
            return JobStatus(
                state_name=KubernetesJobState.Failed.value,
                description=(
                    f"Job reports running pod count as "
                    f"{self.pending_or_running_pod_count}, but no "
                    f"pods could be identified."
                ),
                last_update_epoch_time=self.epoch_time_last_updated,
            )
        else:
            return self.get_active_status_from_pods(
                latest_summary=latest_summary,
                current_pods=self.current_pods,
                most_recent_condition=self.most_recent_condition,
                previous_pod_name=self.previous_pod_name,
                previous_node_name=self.previous_node_name,
                last_update_epoch_time=self.epoch_time_last_updated,
            )

    @classmethod
    def get_active_status_from_pods(
        cls,
        latest_summary: PodSummary,
        current_pods: List[PodSummary],
        most_recent_condition: Optional[str],
        previous_pod_name: Optional[str],
        previous_node_name: Optional[str],
        last_update_epoch_time: float,
    ) -> JobStatus:
        state_name = KubernetesJobState.Running.value
        if latest_summary.node_name is None:
            description = f"Job is running with pod {latest_summary.pod_name}."
        else:
            description = (
                f"Job is running with pod {latest_summary.pod_name} on "
                f"node {latest_summary.node_name}."
            )

        if (
            previous_node_name is not None
            and previous_node_name != latest_summary.node_name
        ):
            description += (
                " The pod was restarted by Kubernetes without Sematic's "
                "intervention, and was assigned to a new Kubernetes node. "
                "This can have many causes."
            )
        elif (
            previous_pod_name is not None
            and previous_pod_name != latest_summary.pod_name
        ):
            description += (
                " The pod was restarted by Kubernetes without Sematic's "
                "intervention, but was not assigned to a new Kubernetes node."
                " This can have many causes."
            )
        if len(current_pods) > 1:
            # multiple pods can sometimes simultaneously be active
            # if pod restart timing works out strangely.
            pod_summaries = [pod.string_summary() for pod in current_pods]
            return JobStatus(
                state_name=KubernetesJobState.Restarting.value,
                description=(
                    f"There are currently {len(current_pods)} "
                    f"pending/runnings pods: {' | '.join(pod_summaries)}"
                ),
                last_update_epoch_time=last_update_epoch_time,
            )

        if latest_summary.phase is not None and latest_summary.phase in dir(
            KubernetesJobState
        ):
            state_name = latest_summary.phase
            if latest_summary.phase == KubernetesJobState.Pending.value:
                if latest_summary.unschedulable_message is not None:
                    description = latest_summary.unschedulable_message
                else:
                    description += f" {latest_summary.container_condition_message}."

        if most_recent_condition is not None:
            description += f" Pod condition is: {most_recent_condition}."
        return JobStatus(
            state_name=state_name,
            description=description,
            last_update_epoch_time=last_update_epoch_time,
        )

    @classmethod
    def _get_job_failed_status(
        cls,
        latest_summary: Optional[PodSummary],
        epoch_time_last_updated: float,
    ):
        state_name = KubernetesJobState.Failed.value
        description = "Job failed. "
        pod_name = latest_summary.pod_name if latest_summary is not None else "UNKNOWN"

        is_premature_0_exit = (
            latest_summary is not None
            and latest_summary.container_exit_code == 0
            and latest_summary.detected_infra_failure
        )
        if is_premature_0_exit:
            description += (
                "The container exited with a 0 exit code, "
                "but Sematic did not record the terminal state from the worker. "
                "Did the code inside the Sematic func contain a forced premature exit "
                "(ex: sys.exit(0), os._exit(0))?"
            )
        elif (
            latest_summary is not None
            and latest_summary.container_condition_message is not None
        ):
            description += latest_summary.container_condition_message + "."

        # Warning instead of error because it's normal for user jobs to fail
        # even when Sematic/the server is healthy.
        logger.warning("Worker pod %s failed: %s", pod_name, description)

        return JobStatus(
            state_name=state_name,
            description=description,
            last_update_epoch_time=epoch_time_last_updated,
        )

    def get_exception_metadata(self) -> Optional[ExceptionMetadata]:
        """
        Returns an `ExceptionMetadata` object in case the job has experienced a
        failure.

        The message is based on pod and container statuses.
        """
        if not self.has_infra_failure:
            return None

        message = "\n".join(
            [
                message
                for message in (
                    self.most_recent_pod_phase_message,
                    self.most_recent_pod_condition_message,
                    self.most_recent_container_condition_message,
                )
                if message is not None
            ]
        )

        return ExceptionMetadata(
            repr=message or "The Kubernetes job state is unknown",
            name=KubernetesError.__name__,
            module=KubernetesError.__module__,
            ancestors=ExceptionMetadata.ancestors_from_exception(KubernetesError),
        )


def _unique_job_id_suffix() -> str:
    """
    Jobs need to have unique names in case of retries.
    """
    return uuid.uuid4().hex[:6]


def _is_none_or_empty(list_: Optional[List]) -> bool:
    """
    Returns True if a list is None or empty, False otherwise.
    """
    return list_ is None or len(list_) == 0


def _v1_pod_precedence_key(pod_summary: PodSummary) -> int:
    """
    To be used as a sorting key when determining the precedence of `V1Pod`s.

    Uses the phase of the pod because the start_time might be None in some phases.
    """
    if pod_summary.phase is None:
        return -1

    return (
        POD_PHASE_PRECEDENCE.index(pod_summary.phase)
        if pod_summary.phase in POD_PHASE_PRECEDENCE
        else -1
    )


def _v1_pod_condition_precedence_key(condition: V1PodCondition) -> Any:
    """
    To be used as a sorting key when determining the precedence of `V1PodCondition`s.

    Unknown conditions are first. True conditions follow. Then False conditions come last.
    """
    key = -1

    if condition.type in POD_CONDITION_PRECEDENCE:
        key = POD_CONDITION_PRECEDENCE.index(condition.type)

        # conditions that are not True have not been achieved yet
        # True conditions are considered to reflect the true state, if any
        if condition.status != "True":
            key += len(POD_CONDITION_PRECEDENCE)

    return key


def _make_final_message(
    condition: str, reason: Optional[str] = None, message: Optional[str] = None
) -> str:
    """
    Returns a human-readable combination of the three messages.
    """
    if not reason and not message:
        return condition
    if reason and message:
        return f"{condition}: {reason}; {message}"
    return f"{condition}: {reason or message}"


def _has_container_failure(container_status: Optional[V1ContainerStatus]) -> bool:
    """
    Returns whether the `V1ContainerStatus` object indicates any failure or abnormality.
    """
    if container_status is None or container_status.state is None:
        return False
    return container_status.state.terminated is not None


def _get_standardized_container_state(
    container_status: Optional[V1ContainerStatus],
) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Tentatively parses out condition, reason, and message strings from the
    `V1ContainerStatus` object.
    """
    if container_status is None or container_status.state is None:
        return "Container state is unknown!", None, None

    state = container_status.state

    if state.waiting is not None:
        return "Container is waiting", state.waiting.reason, state.waiting.message

    if state.running is not None:
        return "Container is running", None, None

    if state.terminated is not None:
        exit_code = _get_container_exit_code_from_status(container_status)
        message = state.terminated.message

        if exit_code is not None:
            # exit code is very useful info, but is not included in
            # the reason/message. Let's add it.
            if message is None:
                message = f"Exit code is {exit_code}"
            else:
                message += f". Exit code is {exit_code}"
        return (
            "Container is terminated",
            state.terminated.reason,
            message,
        )

    return "Container state is unreadable!", None, None


def _get_most_recent_job_condition(
    job: KubernetesExternalJob, k8s_job: V1Job
) -> Optional[str]:
    """
    Returns a human-readable message describing the latest condition for the specified
    job based on the information in the specified `V1Job` payload, falling back to the
    existing latest job condition if there is no new information.
    """
    if (
        k8s_job.status.conditions is None  # type: ignore
        or len(k8s_job.status.conditions) == 0  # type: ignore
    ):
        return job.most_recent_condition

    conditions = sorted(
        k8s_job.status.conditions,  # type: ignore
        key=lambda c: c.last_transition_time,
        reverse=True,
    )

    for condition in conditions:
        if condition.status != "True":
            # we're only interested in True conditions
            continue
        if condition.type in (
            KubernetesJobCondition.Complete.value,
            KubernetesJobCondition.Failed.value,
        ):
            return condition.type

    return job.most_recent_condition


def _get_pods_for_job(
    job: KubernetesExternalJob,
) -> Tuple[Optional[List[V1Pod]], bool]:
    """Get the pod(s) associated with the given job

    Parameters
    ----------
    job:
        The job to get pods for

    Returns
    -------
    A tuple where the first element is the list of pods, if the list can
    be determined. If the list of pods can't be determined due to error,
    the first element will be None.

    The second element of the tuple is a boolean indicating if there was
    an infra failure during pod retrieval (True if there was an error).
    """
    k8s_pods = None
    has_infra_failure = False
    try:
        k8s_pods = kubernetes.client.CoreV1Api().list_namespaced_pod(
            namespace=job.namespace,
            label_selector=f"job-name={job.kubernetes_job_name}",
        )
        logger.debug("K8 pods for job %s:\n%s", job.external_job_id, k8s_pods)

        if _is_none_or_empty(k8s_pods.items):
            return [], has_infra_failure
        return list(k8s_pods.items), has_infra_failure
    except OpenApiException as e:
        has_infra_failure = True
        logger.warning(
            "Got exception while looking for pods for job %s",
            job.external_job_id,
            exc_info=e,
        )
        return None, has_infra_failure


def _get_unschedulable_reason(pod_conditions) -> Optional[str]:
    message = None
    for condition in pod_conditions:
        if condition.type != "PodScheduled" or condition.status == "True":
            continue

        message = (
            f"Pod is not scheduled. Reason: {condition.reason}: {condition.message}. "
            f"Depending on your Kubernetes cluster's configuration and current usage, "
            f"this may or may not resolve itself on its own. Please consult your "
            f"cluster operator."
        )
    return message


def _get_pod_summary(pod: V1Pod) -> PodSummary:
    try:
        node_name = pod.spec.node_name if pod.spec is not None else None
        detected_infra_failure = False
        container_exit_code = None
        if pod.status is None:
            logger.warning("Pod %s has no status", pod.metadata.name)  # type: ignore
            return PodSummary(
                pod_name=pod.metadata.name,  # type: ignore
                detected_infra_failure=detected_infra_failure,
                node_name=node_name,
            )

        unschedulable_reason = None
        if _is_none_or_empty(pod.status.conditions):
            most_recent_condition_message = "Most recent pod condition is unknown"
        else:
            unschedulable_reason = _get_unschedulable_reason(pod.status.conditions)
            most_recent_condition = min(
                pod.status.conditions,  # type: ignore
                key=_v1_pod_condition_precedence_key,
            )
            condition_modifier = (
                "" if most_recent_condition.status == "True" else "NOT "
            )
            most_recent_condition_message = _make_final_message(
                f"Pod condition is {condition_modifier}'{most_recent_condition.type}'",
                most_recent_condition.reason,
                most_recent_condition.message,
            )

            if most_recent_condition.type in POD_FAILURE_PHASES:
                detected_infra_failure = True

        container_restarts = None
        # try to build a message based on the latest container status
        if _is_none_or_empty(pod.status.container_statuses):
            most_recent_container_condition_message = "There is no container!"
            detected_infra_failure = pod.status.phase != "Pending"
        else:
            # there can be only one
            most_recent_container_status = pod.status.container_statuses[
                0
            ]  # type: ignore

            container_exit_code = _get_container_exit_code_from_status(
                most_recent_container_status
            )

            most_recent_container_condition_message = _make_final_message(
                *_get_standardized_container_state(most_recent_container_status)
            )

            if _has_container_failure(most_recent_container_status):
                detected_infra_failure = pod.status.phase != "Pending"

            container_restarts = getattr(
                most_recent_container_status, "restart_count", None
            )

        return PodSummary(
            pod_name=pod.metadata.name,  # type: ignore
            container_restart_count=container_restarts,
            phase=pod.status.phase,
            condition_message=most_recent_condition_message,
            container_condition_message=most_recent_container_condition_message,
            container_exit_code=container_exit_code,
            start_time_epoch_seconds=(
                pod.status.start_time.timestamp()
                if pod.status.start_time is not None
                else None
            ),
            detected_infra_failure=detected_infra_failure,
            unschedulable_message=unschedulable_reason,
            node_name=node_name,
        )
    except Exception as e:
        pod_name = "Unknown"
        try:
            pod_name = pod.metadata.name  # type: ignore
        except Exception as e2:
            logger.error("Pod name could not be determined", exc_info=e2)
        logger.error(
            "Got exception while extracting information from pods: %s",
            pod_name,
            exc_info=e,
        )
        return PodSummary(
            pod_name=pod_name,
            detected_infra_failure=True,
        )


def _get_container_exit_code_from_status(
    container_status: Optional[V1ContainerStatus],
) -> Optional[int]:
    if container_status is None:
        return None
    state = getattr(container_status, "state", None)
    if state is None:
        return None
    terminated = getattr(state, "terminated", None)
    if terminated is None:
        return None
    exit_code = getattr(terminated, "exit_code", None)
    return exit_code


def load_kube_config():
    """Load the kubeconfig either from file or the in-cluster config."""
    global _kubeconfig_loaded
    if _kubeconfig_loaded:
        return
    try:
        kubernetes.config.load_kube_config()  # type: ignore
    except kubernetes.config.config_exception.ConfigException as e1:  # type: ignore
        try:
            kubernetes.config.load_incluster_config()  # type: ignore
        except kubernetes.config.config_exception.ConfigException as e2:  # type: ignore # noqa: E501
            raise RuntimeError("Unable to find kube config:\n{}\n{}".format(e1, e2))
    _kubeconfig_loaded = True


@retry(exceptions=(ApiException, ConnectionError), tries=3, delay=5, jitter=2)
def cancel_job(job: KubernetesExternalJob) -> KubernetesExternalJob:
    """
    Cancel a remote k8s job.
    """
    load_kube_config()
    if not isinstance(job, KubernetesExternalJob):
        raise ValueError(
            f"Expected a {KubernetesExternalJob.__name__}, got a {type(job).__name__}"
        )
    job = refresh_job(job)
    if not job.still_exists:
        logger.info(
            "No need to cancel Kubernetes job %s, as it no longer exists",
            job.external_job_id,
        )
        return job

    try:
        kubernetes.client.BatchV1Api().delete_namespaced_job(
            namespace=job.namespace,
            name=job.kubernetes_job_name,
            grace_period_seconds=0,
            propagation_policy="Background",
        )
    except ApiException as e:
        logging.warning("Error attempting to delete Kubernetes job: %s", e)
        if e.status == 404:
            pass

    job.still_exists = False

    return job


@retry(exceptions=(ApiException, ConnectionError), tries=3, delay=5, jitter=2)
def refresh_job(job: ExternalJob) -> KubernetesExternalJob:
    """Reach out to K8s for updates on the status of the job."""
    load_kube_config()

    if not isinstance(job, KubernetesExternalJob):
        raise ValueError(
            f"Expected a {KubernetesExternalJob.__name__}, got a {type(job).__name__}"
        )

    if not job.still_exists:
        return job

    job.previous_pod_name = job.latest_pod_name()
    job.previous_node_name = job.latest_node_name()

    try:
        k8s_job = kubernetes.client.BatchV1Api().read_namespaced_job_status(
            name=job.kubernetes_job_name, namespace=job.namespace
        )
        logger.debug("K8 job status for job %s:\n%s", job.external_job_id, k8s_job)

    except ApiException as e:
        if e.status == 404:
            logger.warning("Got 404 while looking for job %s", job.external_job_id)
            if not job.has_started:
                return job  # still hasn't started
            else:
                job.still_exists = False
                job.has_infra_failure = True
                return job
        raise e

    if k8s_job.status is None:
        raise ValueError(
            "Received malformed k8 job payload with no status "
            f"for job {job.external_job_id}"
        )

    if not job.has_started:
        # this should never be None once the job has started
        ts = (
            k8s_job.status.start_time.timestamp()
            if k8s_job.status.start_time is not None
            else None
        )
        if ts is None:
            logger.warning(
                "Setting has_started=True for job %s with no start time!",
                job.external_job_id,
            )
        else:
            logger.info(
                "Setting has_started=True for job %s at timestamp %s",
                job.external_job_id,
                ts,
            )
        job.has_started = True
        job.start_time = ts

    # trust the status.active field over the state of pods,
    # as explained in KubernetesExternalJob.is_active()
    job.pending_or_running_pod_count = (
        k8s_job.status.active if k8s_job.status.active is not None else 0  # type: ignore
    )
    job.succeeded_pod_count = (
        k8s_job.status.succeeded  # type: ignore
        if k8s_job.status.succeeded is not None  # type: ignore
        else 0
    )

    job.most_recent_condition = _get_most_recent_job_condition(job, k8s_job)
    pods, had_infra_failure = _get_pods_for_job(job)
    job.has_infra_failure = had_infra_failure
    job.epoch_time_last_updated = time.time()

    if pods is None:
        job.current_pods = []
    else:
        pod_summaries = [_get_pod_summary(pod) for pod in pods]
        job.current_pods = pod_summaries
        most_recent_pod_summary: PodSummary = min(
            pod_summaries, key=_v1_pod_precedence_key
        )
        job.most_recent_pod_phase_message = (
            f"Pod phase is {most_recent_pod_summary.phase}"
        )
        job.most_recent_pod_condition_message = (
            most_recent_pod_summary.condition_message
        )
        job.most_recent_container_condition_message = (
            most_recent_pod_summary.container_condition_message
        )
        job.has_infra_failure = most_recent_pod_summary.detected_infra_failure

    logger.debug("Job %s refreshed: %s", job.external_job_id, job)
    return job


def _schedule_kubernetes_job(
    name: str,
    image: str,
    environment_vars: Dict[str, str],
    namespace: str,
    service_account: str = DEFAULT_WORKER_SERVICE_ACCOUNT,
    api_address_override: Optional[str] = None,
    socketio_address_override: Optional[str] = None,
    resource_requirements: Optional[ResourceRequirements] = None,
    args: Optional[List[str]] = None,
):
    load_kube_config()

    # clone so we can modify without changing the original
    environment_vars = dict(environment_vars)

    if api_address_override is not None:
        environment_vars[
            UserSettingsVar.SEMATIC_API_ADDRESS.value
        ] = api_address_override
    if socketio_address_override is not None:
        environment_vars[
            ServerSettingsVar.SEMATIC_WORKER_SOCKET_IO_ADDRESS.value
        ] = socketio_address_override

    # TODO: Remove this once logging is properly using storage settings.
    # As of this authorship, worker/driver jobs are not getting settings
    # around storage transferred to them, but try to use S3 storage
    # to write logs. The proper fix is to integrate logging into the
    # full storage plugin system so the workers/drivers can be agnostic
    # of where they are writing the logging file bytes to.
    # See: https://github.com/sematic-ai/sematic/issues/579
    s3_bucket = environment_vars.get(S3StorageSettingsVar.AWS_S3_BUCKET.value, None)
    if s3_bucket is None:
        s3_bucket = get_plugin_setting(
            S3Storage, S3StorageSettingsVar.AWS_S3_BUCKET, None
        )
        if s3_bucket is not None:
            environment_vars[S3StorageSettingsVar.AWS_S3_BUCKET.value] = s3_bucket

    args = args if args is not None else []
    node_selector = {}
    resource_requests = {}
    volumes = []
    volume_mounts = []
    secret_env_vars = []
    tolerations = []

    if resource_requirements is not None:
        node_selector = resource_requirements.kubernetes.node_selector
        resource_requests = resource_requirements.kubernetes.requests
        volume_info = _volume_secrets(resource_requirements.kubernetes.secret_mounts)

        if volume_info is not None:
            volume, mount = volume_info
            volumes.append(volume)
            volume_mounts.append(mount)

        if resource_requirements.kubernetes.mount_expanded_shared_memory:
            volume, mount = _shared_memory()
            volumes.append(volume)
            volume_mounts.append(mount)

        secret_env_vars.extend(
            _environment_secrets(resource_requirements.kubernetes.secret_mounts)
        )
        tolerations = [
            kubernetes.client.V1Toleration(  # type: ignore
                **toleration.to_api_keyword_args()  # type: ignore
            )
            for toleration in resource_requirements.kubernetes.tolerations
        ]

        logger.debug("kubernetes node_selector %s", node_selector)
        logger.debug("kubernetes resource requests %s", resource_requests)
        logger.debug("kubernetes volumes: %s", volumes)
        logger.debug("kubernetes volume mounts: %s", volume_mounts)
        logger.debug("kubernetes environment secrets: %s", secret_env_vars)
        logger.debug("kubernetes tolerations: %s", tolerations)

    pod_name_env_var = kubernetes.client.V1EnvVar(  # type: ignore
        name=KUBERNETES_POD_NAME_ENV_VAR,
        value_from=kubernetes.client.V1EnvVarSource(  # type: ignore
            field_ref=kubernetes.client.V1ObjectFieldSelector(  # type: ignore
                field_path="metadata.name",
            )
        ),
    )

    # See client documentation here:
    # https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1Job.md
    job = kubernetes.client.V1Job(  # type: ignore
        api_version="batch/v1",
        kind="Job",
        metadata=kubernetes.client.V1ObjectMeta(name=name),  # type: ignore
        spec=kubernetes.client.V1JobSpec(  # type: ignore
            template=kubernetes.client.V1PodTemplateSpec(  # type: ignore
                metadata=kubernetes.client.V1ObjectMeta(  # type: ignore
                    annotations={
                        "cluster-autoscaler.kubernetes.io/safe-to-evict": "false"
                    },
                ),
                spec=kubernetes.client.V1PodSpec(  # type: ignore
                    node_selector=node_selector,
                    containers=[
                        kubernetes.client.V1Container(  # type: ignore
                            name=name,
                            image=image,
                            args=args,
                            env=[
                                kubernetes.client.V1EnvVar(  # type: ignore
                                    name=CONTAINER_IMAGE_ENV_VAR,
                                    value=image,
                                ),
                                kubernetes.client.V1EnvVar(  # type: ignore
                                    name=ON_WORKER_ENV_VAR,
                                    value="1",
                                ),
                                kubernetes.client.V1EnvVar(  # type: ignore
                                    # this makes it such that stdout and stderr
                                    # are less likely to interleave substantially
                                    # out-of-order from when they were written to
                                    name="PYTHONUNBUFFERED",
                                    value="1",
                                ),
                                pod_name_env_var,
                            ]
                            + [
                                kubernetes.client.V1EnvVar(  # type: ignore
                                    name=name,
                                    value=str(value),
                                )
                                for name, value in environment_vars.items()
                            ]
                            + secret_env_vars,
                            volume_mounts=volume_mounts,
                            resources=(
                                kubernetes.client.V1ResourceRequirements(  # type: ignore
                                    limits=resource_requests,
                                    requests=resource_requests,
                                )
                            ),
                        )
                    ],
                    volumes=volumes,
                    tolerations=tolerations,
                    restart_policy="Never",
                    service_account_name=service_account,
                ),
            ),
            backoff_limit=0,
            ttl_seconds_after_finished=3600,
        ),
    )

    kubernetes.client.BatchV1Api().create_namespaced_job(  # type: ignore
        namespace=namespace, body=job
    )


def schedule_resolution_job(
    resolution_id: str,
    image: str,
    user_settings: Dict[str, str],
    max_parallelism: Optional[int] = None,
    rerun_from: Optional[str] = None,
) -> ExternalJob:

    namespace = get_server_setting(ServerSettingsVar.KUBERNETES_NAMESPACE)
    service_account = get_server_setting(
        ServerSettingsVar.SEMATIC_WORKER_KUBERNETES_SA, DEFAULT_WORKER_SERVICE_ACCOUNT
    )
    api_address_override = get_server_setting(
        ServerSettingsVar.SEMATIC_WORKER_API_ADDRESS, None
    )
    socketio_address_override = get_server_setting(
        ServerSettingsVar.SEMATIC_WORKER_SOCKET_IO_ADDRESS, None
    )

    external_job = KubernetesExternalJob.new(
        try_number=0,
        run_id=resolution_id,
        namespace=namespace,
        job_type=JobType.driver,
    )

    logger.info("Scheduling job %s", external_job.kubernetes_job_name)

    args = ["--run_id", resolution_id, "--resolve"]

    if max_parallelism is not None:
        args += ["--max-parallelism", str(max_parallelism)]

    if rerun_from is not None:
        args += ["--rerun-from", rerun_from]

    _schedule_kubernetes_job(
        name=external_job.kubernetes_job_name,
        image=image,
        environment_vars=user_settings,
        namespace=namespace,
        service_account=service_account,
        api_address_override=api_address_override,
        socketio_address_override=socketio_address_override,
        resource_requirements=RESOLUTION_RESOURCE_REQUIREMENTS,
        args=args,
    )
    return external_job


def schedule_run_job(
    run_id: str,
    image: str,
    user_settings: Dict[str, str],
    resource_requirements: Optional[ResourceRequirements] = None,
    try_number: int = 0,
) -> ExternalJob:
    """Schedule a job on k8s for a calculator execution."""
    # "User" in this case is the server.
    namespace = get_server_setting(ServerSettingsVar.KUBERNETES_NAMESPACE)
    service_account = get_server_setting(
        ServerSettingsVar.SEMATIC_WORKER_KUBERNETES_SA, DEFAULT_WORKER_SERVICE_ACCOUNT
    )
    api_address_override = get_server_setting(
        ServerSettingsVar.SEMATIC_WORKER_API_ADDRESS, None
    )
    socketio_address_override = get_server_setting(
        ServerSettingsVar.SEMATIC_WORKER_SOCKET_IO_ADDRESS, None
    )

    external_job = KubernetesExternalJob.new(
        try_number, run_id, namespace, JobType.worker
    )
    logger.info(
        "Scheduling job %s with image %s", external_job.kubernetes_job_name, image
    )
    args = ["--run_id", run_id]

    _schedule_kubernetes_job(
        name=external_job.kubernetes_job_name,
        image=image,
        environment_vars=user_settings,
        namespace=namespace,
        service_account=service_account,
        api_address_override=api_address_override,
        socketio_address_override=socketio_address_override,
        resource_requirements=resource_requirements,
        args=args,
    )
    return external_job


def _volume_secrets(
    secret_mount: KubernetesSecretMount,
) -> Optional[Tuple[V1Volume, V1VolumeMount]]:
    """Configure a volume and corresponding mount for secrets requested for a func.

    Parameters
    ----------
    secret_mount:
        The request for how to mount secrets into the pod for a Sematic func

    Returns
    -------
    None if no file secrets were requested. Otherwise, a volume and a volume mount
    for the secrets requested.
    """
    if len(secret_mount.file_secrets) == 0:
        return None

    for relative_path in secret_mount.file_secrets.values():
        if pathlib.Path(relative_path).is_absolute():
            raise ValueError(
                f"Cannot mount secret to absolute path '{relative_path}'; "
                "paths must be relative."
            )

    volume_name = "sematic-func-secrets-volume"

    volume = V1Volume(
        name=volume_name,
        secret=kubernetes.client.V1SecretVolumeSource(  # type: ignore
            items=[
                kubernetes.client.V1KeyToPath(  # type: ignore
                    key=key,
                    path=relative_path,
                )
                for key, relative_path in secret_mount.file_secrets.items()
            ],
            optional=False,
            secret_name=KUBERNETES_SECRET_NAME,
        ),
    )

    mount = V1VolumeMount(
        mount_path=secret_mount.file_secret_root_path,
        name=volume_name,
        read_only=True,
    )

    return volume, mount


def _environment_secrets(
    secret_mount: KubernetesSecretMount,
) -> List[kubernetes.client.V1EnvVar]:  # type: ignore
    """Configure environment variables for secrets requested for a func

    Parameters
    ----------
    secret_mount:
        The request for how to mount secrets into the pod for a Sematic func

    Returns
    -------
    A list of configurations for Kubernetes environment variables that will get
    their values from the "sematic-func-secrets" Kubernetes secret.
    """
    env_vars = []
    for key, env_var_name in secret_mount.environment_secrets.items():
        env_vars.append(
            kubernetes.client.V1EnvVar(  # type: ignore
                name=env_var_name,
                value_from=kubernetes.client.V1EnvVarSource(  # type: ignore
                    secret_key_ref=kubernetes.client.V1SecretKeySelector(  # type: ignore
                        name=KUBERNETES_SECRET_NAME,
                        key=key,
                    )
                ),
            )
        )
    return env_vars


def _shared_memory() -> Tuple[V1Volume, V1VolumeMount]:
    """
    Returns a memory-backed shared memory partition and mount with a default size.
    """
    # the "Memory" medium cannot have a size_limit specified by default;
    # it requires the SizeMemoryBackedVolumes feature gate be activated by the
    # cluster admin - please see
    # https://kubernetes.io/docs/reference/command-line-tools-reference/feature-gates/
    # without that, it will default to half the available memory
    empty_dir = kubernetes.client.V1EmptyDirVolumeSource(
        medium="Memory",
    )

    volume_name = "expanded-shared-memory-volume"

    volume = V1Volume(name=volume_name, empty_dir=empty_dir)
    volume_mount = V1VolumeMount(mount_path="/dev/shm", name=volume_name)

    return volume, volume_mount
