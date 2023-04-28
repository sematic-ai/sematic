# Standard Library
import logging
import pathlib
import time
import uuid
from dataclasses import replace
from typing import Any, Dict, List, Optional, Tuple

# Third-party
import kubernetes
from kubernetes.client.exceptions import ApiException, OpenApiException
from kubernetes.client.models import (
    V1ContainerStatus,
    V1Pod,
    V1PodCondition,
    V1Volume,
    V1VolumeMount,
)
from urllib3.exceptions import ConnectionError

# Sematic
from sematic.config.config import KUBERNETES_POD_NAME_ENV_VAR, ON_WORKER_ENV_VAR
from sematic.config.server_settings import (
    ServerSettingsVar,
    get_bool_server_setting,
    get_server_setting,
)
from sematic.config.settings import get_plugin_setting
from sematic.config.user_settings import UserSettingsVar
from sematic.container_images import CONTAINER_IMAGE_ENV_VAR
from sematic.db.models.factories import make_job
from sematic.db.models.job import Job
from sematic.plugins.storage.s3_storage import S3Storage, S3StorageSettingsVar
from sematic.resolvers.resource_requirements import (
    KUBERNETES_SECRET_NAME,
    KubernetesResourceRequirements,
    KubernetesSecretMount,
    ResourceRequirements,
)
from sematic.scheduling.job_details import (
    JobDetails,
    JobKind,
    JobStatus,
    KubernetesJobState,
    PodSummary,
)
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
def cancel_job(job: Job) -> Job:
    """
    Cancel a remote k8s job.
    """
    load_kube_config()
    if not isinstance(job, Job):
        raise ValueError(f"Expected a {Job.__name__}, got a {type(job).__name__}")
    details = job.details
    if not details.still_exists:
        details.canceled = True
        job.update_status(details.get_status(time.time()))
        logger.info(
            "No need to cancel Kubernetes job %s, as it no longer exists",
            job.identifier(),
        )
        return job

    try:
        kubernetes.client.BatchV1Api().delete_namespaced_job(
            namespace=job.namespace,
            name=job.name,
            grace_period_seconds=0,
            propagation_policy="Background",
        )
    except ApiException as e:
        logging.warning("Error attempting to delete Kubernetes job: %s", e)
        if e.status == 404:
            pass

    details.still_exists = False
    details.canceled = True
    job.details = details

    return job


@retry(exceptions=(ApiException, ConnectionError), tries=3, delay=5, jitter=2)
def refresh_job(job: Job) -> Job:
    """Reach out to K8s for updates on the status of the job."""
    load_kube_config()
    details = job.details
    details.previous_pod_name = details.latest_pod_name()
    details.previous_node_name = details.latest_node_name()

    if not isinstance(job, Job):
        raise ValueError(f"Expected a {Job.__name__}, got a {type(job).__name__}")

    try:
        k8s_job = kubernetes.client.BatchV1Api().read_namespaced_job_status(
            name=job.name, namespace=job.namespace
        )
        logger.debug("K8 job status for job %s:\n%s", job.identifier(), k8s_job)

    except ApiException as e:
        if e.status == 404:
            logger.warning("Got 404 while looking for job %s", job.identifier())
            if not job.details.has_started:
                job.update_status(
                    replace(
                        job.latest_status,
                        last_updated_epoch_seconds=time.time(),
                    )
                )
                return job  # still hasn't started
            else:
                details.still_exists = False
                job.details = details
                job.update_status(details.get_status(time.time()))
                return job
        raise e

    try:
        pods, has_infra_failure = _get_pods_for_job(job)
        pods = pods or []
        details.current_pods = [_get_pod_summary(pod) for pod in pods]
        details.has_infra_failure |= has_infra_failure
    except Exception:
        logger.exception("Exception getting pods for job %s", job.identifier())
        details.current_pods = []

    latest_pod_summary = details.latest_pod_summary()
    if latest_pod_summary is None:
        details.has_infra_failure = True
    else:
        details.has_infra_failure |= latest_pod_summary.has_infra_failure

    if k8s_job.status is None:
        raise ValueError(
            "Received malformed k8 job payload with no status "
            f"for job {job.namespace}/{job.name}"
        )

    if not job.details.has_started:
        # this should never be None once the job has started
        ts = (
            k8s_job.status.start_time.timestamp()
            if k8s_job.status.start_time is not None
            else None
        )
        if ts is None:
            logger.warning(
                "Setting has_started=True for job %s with no start time!",
                job.identifier(),
            )
        else:
            logger.info(
                "Setting has_started=True for job %s at timestamp %s",
                job.identifier(),
                ts,
            )
        details.has_started = True
        details.start_time = ts

    # Trust the status.active field over the state of pods. According to the docs:
    # github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1JobStatus.md
    # a job's "active" field holds the number of pending or running pods.
    # This should be a more reliable measure of whether the job is still
    # active than the number of succeeded or failed pods, as during pod
    # evictions (which don't stop the job completely, but do stop the pod),
    # a pod can briefly show up as failed even when another one is
    # going to be scheduled in its place.
    details.pending_or_running_pod_count = (
        k8s_job.status.active if k8s_job.status.active is not None else 0  # type: ignore
    )
    details.succeeded_pod_count = (
        k8s_job.status.succeeded  # type: ignore
        if k8s_job.status.succeeded is not None  # type: ignore
        else 0
    )

    job.details = details

    job.update_status(details.get_status(time.time()))

    logger.debug("Job %s refreshed: %s", job.identifier(), job)
    return job


def _get_pod_summary(pod: V1Pod) -> PodSummary:
    try:
        node_name = pod.spec.node_name if pod.spec is not None else None
        has_infra_failure = False
        container_exit_code = None
        if pod.status is None:
            logger.warning("Pod %s has no status", pod.metadata.name)  # type: ignore
            return PodSummary(
                pod_name=pod.metadata.name,  # type: ignore
                has_infra_failure=has_infra_failure,
                node_name=node_name,
            )

        unschedulable_reason = None
        most_recent_condition = None
        if _is_none_or_empty(pod.status.conditions):
            most_recent_condition_message = "Most recent pod condition is unknown"
            most_recent_condition_name = "Unknown"
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
            most_recent_condition_name = (
                f"{condition_modifier}{most_recent_condition.type}".replace(
                    "NOT ", "Not"
                )
            )

            if most_recent_condition.type in POD_FAILURE_PHASES:
                has_infra_failure = True

        container_restarts = None
        # try to build a message based on the latest container status
        if _is_none_or_empty(pod.status.container_statuses):
            most_recent_container_condition_message = "There is no container!"
            has_infra_failure = pod.status.phase != "Pending"
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
                has_infra_failure = pod.status.phase != "Pending"

            container_restarts = getattr(
                most_recent_container_status, "restart_count", None
            )

        return PodSummary(
            pod_name=pod.metadata.name,  # type: ignore
            container_restart_count=container_restarts,
            phase=pod.status.phase,
            condition_message=most_recent_condition_message,
            condition=most_recent_condition_name,
            container_condition_message=most_recent_container_condition_message,
            container_exit_code=container_exit_code,
            start_time_epoch_seconds=(
                pod.status.start_time.timestamp()
                if pod.status.start_time is not None
                else None
            ),
            has_infra_failure=has_infra_failure,
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
            has_infra_failure=True,
        )


def _get_pods_for_job(
    job: Job,
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
            label_selector=f"job-name={job.name}",
        )
        logger.debug("K8 pods for job %s:\n%s", job.identifier(), k8s_pods)

        if _is_none_or_empty(k8s_pods.items):
            return [], has_infra_failure
        return list(k8s_pods.items), has_infra_failure
    except OpenApiException as e:
        has_infra_failure = True
        logger.warning(
            "Got exception while looking for pods for job %s",
            job.identifier(),
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
            f"this may or may not resolve itself on its own via autoscaling or resource "
            f"reclamation. Please consult your cluster operator."
        )
    return message


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
    security_context = None

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

        if resource_requirements.kubernetes.security_context is not None:
            allow_customization = get_bool_server_setting(
                ServerSettingsVar.ALLOW_CUSTOM_SECURITY_CONTEXTS, False
            )
            if not allow_customization:
                raise ValueError(
                    "User tried to customize the security context for their "
                    "Sematic function, but ALLOW_CUSTOM_SECURITY_CONTEXTS is "
                    "not enabled."
                )
            sc = resource_requirements.kubernetes.security_context
            security_context = kubernetes.client.V1SecurityContext(
                allow_privilege_escalation=sc.allow_privilege_escalation,
                privileged=sc.privileged,
                capabilities=kubernetes.client.V1Capabilities(
                    add=sc.capabilities.add, drop=sc.capabilities.drop
                ),
            )

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
        logger.debug("kubernetes security context: %s", security_context)

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
                            security_context=security_context,
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
) -> Job:

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

    job = make_job(
        namespace=namespace,
        name=f"sematic-driver-{resolution_id}",
        run_id=resolution_id,
        status=JobStatus(
            state=KubernetesJobState.Requested,
            message=(
                "Resolution has been requested by Sematic but "
                "not yet acknowledged by Kubernetes"
            ),
            last_updated_epoch_seconds=time.time(),
        ),
        details=JobDetails(try_number=0),
        kind=JobKind.resolver,
    )

    logger.info("Scheduling job %s", job.identifier())

    args = ["--run_id", resolution_id, "--resolve"]

    if max_parallelism is not None:
        args += ["--max-parallelism", str(max_parallelism)]

    if rerun_from is not None:
        args += ["--rerun-from", rerun_from]

    _schedule_kubernetes_job(
        name=job.name,
        image=image,
        environment_vars=user_settings,
        namespace=namespace,
        service_account=service_account,
        api_address_override=api_address_override,
        socketio_address_override=socketio_address_override,
        resource_requirements=RESOLUTION_RESOURCE_REQUIREMENTS,
        args=args,
    )
    return job


def schedule_run_job(
    run_id: str,
    image: str,
    user_settings: Dict[str, str],
    resource_requirements: Optional[ResourceRequirements] = None,
    try_number: int = 0,
) -> Job:
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

    job = make_job(
        namespace=namespace,
        name=f"sematic-worker-{run_id}-{_unique_job_id_suffix()}",
        run_id=run_id,
        status=JobStatus(
            state=KubernetesJobState.Requested,
            message=(
                "Run has been requested by Sematic but not yet acknowledged by Kubernetes"
            ),
            last_updated_epoch_seconds=time.time(),
        ),
        details=JobDetails(try_number=try_number),
        kind=JobKind.run,
    )
    logger.info("Scheduling job %s with image %s", job.identifier(), image)
    args = ["--run_id", run_id]

    _schedule_kubernetes_job(
        name=job.name,
        image=image,
        environment_vars=user_settings,
        namespace=namespace,
        service_account=service_account,
        api_address_override=api_address_override,
        socketio_address_override=socketio_address_override,
        resource_requirements=resource_requirements,
        args=args,
    )
    return job


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
