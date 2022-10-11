# Standard Library
import logging
import pathlib
import uuid
from dataclasses import dataclass
from enum import Enum, unique
from typing import Dict, List, Optional, Tuple

# Third-party
import kubernetes
from kubernetes.client.exceptions import ApiException
from urllib3.exceptions import ConnectionError

# Sematic
from sematic.config import (
    KUBERNETES_POD_NAME_ENV_VAR,
    ON_WORKER_ENV_VAR,
    SettingsVar,
    get_user_settings,
)
from sematic.container_images import CONTAINER_IMAGE_ENV_VAR
from sematic.resolvers.resource_requirements import (
    KUBERNETES_SECRET_NAME,
    KubernetesResourceRequirements,
    KubernetesSecretMount,
    ResourceRequirements,
)
from sematic.scheduling.external_job import KUBERNETES_JOB_KIND, ExternalJob, JobType
from sematic.utils.retry import retry

logger = logging.getLogger(__name__)
_kubeconfig_loaded = False


RESOLUTION_RESOURCE_REQUIREMENTS = ResourceRequirements(
    kubernetes=KubernetesResourceRequirements(
        requests={"cpu": "500m", "memory": "2Gi"},
    )
)


@unique
class KubernetesJobCondition(Enum):
    Complete = "Complete"
    Failed = "Failed"


@dataclass
class KubernetesExternalJob(ExternalJob):

    # See
    # github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1JobStatus.md
    # and: https://kubernetes.io/docs/concepts/workloads/controllers/job/
    # Explanation of k8s status conditions:
    # https://maelvls.dev/kubernetes-conditions/

    # pending_or_running_pod_count is the "active" property.
    pending_or_running_pod_count: int
    succeeded_pod_count: int
    most_recent_condition: Optional[str]
    has_started: bool
    still_exists: bool

    @classmethod
    def new(
        cls, try_number: int, run_id: str, namespace: str, job_type: JobType
    ) -> "KubernetesExternalJob":
        """Get a job with an appropriate configuration for having just started"""
        return KubernetesExternalJob(
            kind=KUBERNETES_JOB_KIND,
            try_number=try_number,
            external_job_id=cls.make_external_job_id(run_id, namespace, job_type),
            pending_or_running_pod_count=1,
            succeeded_pod_count=0,
            has_started=False,
            still_exists=True,
            most_recent_condition=None,
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
        # According to the docs:
        # github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1JobStatus.md
        # a job's "active" field holds the number of pending or running pods.
        # This should be a more reliable measure of whether the job is still
        # active than the number of succeeded or failed pods, as during pod
        # evictions (which don't stop the job completely, but do stop the pod),
        # a pod can briefly show up as failed even when another one is
        # going to be scheduled in its place.
        if not self.has_started:
            return True
        if not self.still_exists:
            return False
        if self.most_recent_condition is None:
            return True
        if self.most_recent_condition in (
            KubernetesJobCondition.Complete.value,
            KubernetesJobCondition.Failed.value,
        ):
            return False
        return self.succeeded_pod_count == 0 and self.pending_or_running_pod_count > 0


def _unique_job_id_suffix() -> str:
    """
    Jobs need to have unique names in case of retries.
    """
    return uuid.uuid4().hex[:6]


def load_kube_config():
    """Load the kubeconfig either from file or the in-cluster config"""
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
    """Reach out to K8s for updates on the status of the job"""
    load_kube_config()
    if not isinstance(job, KubernetesExternalJob):
        raise ValueError(
            f"Expected a {KubernetesExternalJob.__name__}, got a {type(job).__name__}"
        )
    try:
        k8s_job = kubernetes.client.BatchV1Api().read_namespaced_job_status(
            name=job.kubernetes_job_name, namespace=job.namespace
        )
    except ApiException as e:
        if e.status == 404:
            logger.error("Got 404 looking for %s", job.external_job_id)
            if not job.has_started:
                return job  # still hasn't started
            else:
                job.still_exists = False
                return job
        raise e
    logger.error("Setting has_started=True for %s", job.external_job_id)
    job.has_started = True
    job.pending_or_running_pod_count = (
        k8s_job.status.active if k8s_job.status.active is not None else 0  # type: ignore
    )
    job.succeeded_pod_count = (
        k8s_job.status.succeeded  # type: ignore
        if k8s_job.status.succeeded is not None  # type: ignore
        else 0
    )
    if (
        k8s_job.status.conditions is not None  # type: ignore
        and len(k8s_job.status.conditions) > 1  # type: ignore
    ):
        conditions = sorted(
            k8s_job.status.conditions,  # type: ignore
            key=lambda c: c.lastTransitionTime,
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
                job.most_recent_condition = condition.type
    return job


def _schedule_kubernetes_job(
    name: str,
    image: str,
    environment_vars: Dict[str, str],
    namespace: str,
    resource_requirements: Optional[ResourceRequirements] = None,
    args: Optional[List[str]] = None,
):
    load_kube_config()
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
        logger.debug("kubernetes volumes and mounts: %s, %s", volumes, volume_mounts)
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
) -> ExternalJob:
    namespace = get_user_settings(SettingsVar.KUBERNETES_NAMESPACE)
    external_job = KubernetesExternalJob.new(
        try_number=0,
        run_id=resolution_id,
        namespace=namespace,
        job_type=JobType.driver,
    )
    logger.info("Scheduling job %s", external_job.kubernetes_job_name)
    args = ["--run_id", resolution_id, "--resolve"]
    _schedule_kubernetes_job(
        name=external_job.kubernetes_job_name,
        image=image,
        environment_vars=user_settings,
        namespace=namespace,
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
    namespace = get_user_settings(SettingsVar.KUBERNETES_NAMESPACE)
    external_job = KubernetesExternalJob.new(
        try_number, run_id, namespace, JobType.worker
    )
    logger.info("Scheduling job %s", external_job.kubernetes_job_name)
    args = ["--run_id", run_id]

    _schedule_kubernetes_job(
        name=external_job.kubernetes_job_name,
        image=image,
        environment_vars=user_settings,
        namespace=namespace,
        resource_requirements=resource_requirements,
        args=args,
    )
    return external_job


def _volume_secrets(
    secret_mount: KubernetesSecretMount,
) -> Optional[  # type: ignore
    Tuple[kubernetes.client.V1Volume, kubernetes.client.V1VolumeMount]
]:
    """Configure a volume and corresponding mount for secrets requested for a func

    Parameters
    ----------
    secret_mount:
        The request for how to mount secrets into the pod for a Sematic func

    Returns
    -------
    None if no file secrets were requested. Otherwise a volume and a volume mount
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

    volume = kubernetes.client.V1Volume(  # type: ignore
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

    mount = kubernetes.client.V1VolumeMount(  # type: ignore
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
