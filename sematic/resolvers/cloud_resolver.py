# Standard Library
import enum
import logging
import pathlib
from typing import Dict, List, Optional, Tuple

# Third-party
import cloudpickle
import kubernetes

# Sematic
import sematic.api_client as api_client
import sematic.storage as storage
from sematic.abstract_future import AbstractFuture, FutureState
from sematic.config import ON_WORKER_ENV_VAR
from sematic.container_images import CONTAINER_IMAGE_ENV_VAR, get_image_uri
from sematic.db.models.artifact import Artifact
from sematic.db.models.edge import Edge
from sematic.db.models.factories import get_artifact_value
from sematic.db.models.resolution import ResolutionKind
from sematic.db.models.run import Run
from sematic.resolvers.local_resolver import LocalResolver, make_edge_key
from sematic.resolvers.resource_requirements import (
    KUBERNETES_SECRET_NAME,
    KubernetesSecretMount,
    ResourceRequirements,
)
from sematic.user_settings import SettingsVar, get_all_user_settings, get_user_settings

logger = logging.getLogger(__name__)


class CloudResolver(LocalResolver):
    """
    Resolves a pipeline on a Kubernetes cluster.

    Parameters
    ----------
    detach: Optional[bool]
        Defaults to `True`.

        When `True`, the driver job will run on the remote cluster. This is the so
        called `fire-and-forget` mode. The shell prompt will return as soon as
        the driver job as been submitted.

        When `False`, the driver job runs on the local machine. The shell prompt
        will return when the entire pipeline has completed.
    """

    def __init__(self, detach: bool = True, is_running_remotely: bool = False):
        super().__init__(detach=detach)

        try:
            kubernetes.config.load_kube_config()  # type: ignore
        except kubernetes.config.config_exception.ConfigException as e1:  # type: ignore
            try:
                kubernetes.config.load_incluster_config()  # type: ignore
            except kubernetes.config.config_exception.ConfigException as e2:  # type: ignore # noqa: E501
                raise RuntimeError("Unable to find kube config:\n{}\n{}".format(e1, e2))

        # TODO: Replace this with a cloud storage engine
        self._store_artifacts = True

        self._output_artifacts_by_run_id: Dict[str, Artifact] = {}
        self._is_running_remotely = is_running_remotely

    def set_graph(self, runs: List[Run], artifacts: List[Artifact], edges: List[Edge]):
        """
        Set the graph to an existing graph.

        This is mostly used in `worker.py` to be able to start from previously created
        graph.
        """
        if len(self._runs) > 0:
            raise RuntimeError("Cannot override a graph")

        self._runs = {run.id: run for run in runs}
        self._artifacts = {artifact.id: artifact for artifact in artifacts}
        self._edges = {make_edge_key(edge): edge for edge in edges}

    def _get_resolution_image(self) -> Optional[str]:
        return get_image_uri()

    def _get_resolution_kind(self, detached) -> ResolutionKind:
        return ResolutionKind.KUBERNETES if detached else ResolutionKind.LOCAL

    def _create_resolution(self, root_future_id, detached):
        if self._is_running_remotely:
            # resolution should have been crated prior to the resolver
            # actually starting its remote resolution.
            return
        super()._create_resolution(root_future_id, detached)

    def _detach_resolution(self, future: AbstractFuture) -> str:
        run = self._populate_run_and_artifacts(future)
        self._save_graph()
        self._create_resolution(future.id, detached=True)
        run.root_id = future.id

        api_client.notify_pipeline_update(run.calculator_path)

        job_name = _make_job_name(future, JobType.driver)
        # SUBMIT ORCHESTRATOR JOB
        _schedule_job(future.id, job_name, resolve=True)

        return run.id

    def _schedule_future(self, future: AbstractFuture) -> None:
        self._set_future_state(future, FutureState.SCHEDULED)
        job_name = _make_job_name(future, JobType.worker)
        _schedule_job(
            future.id,
            job_name,
            resolve=False,
            resource_requirements=future.props.resource_requirements,
        )

    def _wait_for_scheduled_run(self) -> None:
        run_id = self._wait_for_any_inline_run() or self._wait_for_any_remote_job()

        if run_id is None:
            return

        self._process_run_output(run_id)

    def _process_run_output(self, run_id: str):
        self._refresh_graph(run_id)

        run = self._get_run(run_id)

        future = next(future for future in self._futures if future.id == run.id)

        if run.future_state not in {FutureState.RESOLVED.value, FutureState.RAN.value}:
            self._handle_future_failure(
                future, Exception("Run failed, see exception in the UI.")
            )

        if run.nested_future_id is not None:
            pickled_nested_future = storage.get(
                make_nested_future_storage_key(run.nested_future_id)
            )
            value = cloudpickle.loads(pickled_nested_future)

        else:
            output_edge = self._get_output_edges(run.id)[0]
            output_artifact = self._artifacts[output_edge.artifact_id]
            self._output_artifacts_by_run_id[run.id] = output_artifact
            value = get_artifact_value(output_artifact)

        self._update_future_with_value(future, value)

    def _get_output_artifact(self, run_id: str) -> Optional[Artifact]:
        return self._output_artifacts_by_run_id.get(run_id)

    def _future_did_fail(self, failed_future: AbstractFuture) -> None:
        # Unlike LocalResolver._future_did_fail, we only care about
        # failing parent futures since runs are marked FAILED by worker.py
        if failed_future.state == FutureState.NESTED_FAILED:
            super()._future_did_fail(failed_future)

    def _refresh_graph(self, run_id):
        """
        Refresh graph for run ID.

        Will only refresh artifacts and edges directly connected to run
        """
        runs, artifacts, edges = api_client.get_graph(run_id)

        for run in runs:
            self._runs[run.id] = run

        for artifact in artifacts:
            self._artifacts[artifact.id] = artifact

        for edge in edges:
            self._edges[make_edge_key(edge)] = edge

    def _wait_for_any_inline_run(self) -> Optional[str]:
        return next(
            (
                future.id
                for future in self._futures
                if future.props.inline and future.state == FutureState.SCHEDULED
            ),
            None,
        )

    def _wait_for_any_remote_job(self) -> Optional[str]:
        job_names = [
            _make_job_name(future, JobType.worker)
            for future in self._futures
            if not future.props.inline and future.state == FutureState.SCHEDULED
        ]

        if len(job_names) == 0:
            return None

        while True:
            watch = kubernetes.watch.Watch()  # type: ignore

            for event in watch.stream(
                kubernetes.client.BatchV1Api().list_namespaced_job,  # type: ignore
                namespace=get_user_settings(SettingsVar.KUBERNETES_NAMESPACE),
                label_selector="job-name in ({0})".format(", ".join(job_names)),
            ):
                job = event["object"]

                if job.status.succeeded or job.status.failed:
                    watch.stop()
                    return _get_run_id_from_name(job.metadata.name)


class JobType(enum.Enum):
    driver = "driver"
    worker = "worker"


def make_nested_future_storage_key(future_id: str) -> str:
    return "futures/{}".format(future_id)


def _make_job_name(future: AbstractFuture, job_type: JobType) -> str:
    """
    Make K8s job name.

    Please keep in sync with `_get_run_id_from_name`.
    """
    job_name = "-".join(("sematic", job_type.value, future.id))
    return job_name


def _get_run_id_from_name(job_name: str) -> str:
    """
    Extract run ID from K8s job name.

    Should be the reverse of `_make_job_name`.
    """
    return job_name.split("-")[-1]


def _schedule_job(
    run_id: str,
    name: str,
    resource_requirements: Optional[ResourceRequirements] = None,
    resolve: bool = False,
):
    logger.info("Scheduling job %s", name)
    args = ["--run_id", run_id]

    if resolve:
        args.append("--resolve")

    image = get_image_uri()

    node_selector = {}
    resource_requests = {}
    volumes = []
    volume_mounts = []
    secret_env_vars = []
    if (
        resource_requirements is not None
        and resource_requirements.kubernetes is not None
    ):
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
        logger.debug("kubernetes node_selector %s", node_selector)
        logger.debug("kubernetes resource requests %s", resource_requests)
        logger.debug("kubernetes volumes and mounts: %s, %s", volumes, volume_mounts)
        logger.debug("kubernetes environment secrets: %s", secret_env_vars)

    job = kubernetes.client.V1Job(  # type: ignore
        api_version="batch/v1",
        kind="Job",
        metadata=kubernetes.client.V1ObjectMeta(name=name),  # type: ignore
        spec=kubernetes.client.V1JobSpec(  # type: ignore
            template=kubernetes.client.V1PodTemplateSpec(  # type: ignore
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
                            ]
                            + [
                                kubernetes.client.V1EnvVar(  # type: ignore
                                    name=name,
                                    value=str(value),
                                )
                                for name, value in get_all_user_settings().items()
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
                    tolerations=[],
                    restart_policy="Never",
                ),
            ),
            backoff_limit=0,
            ttl_seconds_after_finished=3600,
        ),
    )

    kubernetes.client.BatchV1Api().create_namespaced_job(  # type: ignore
        namespace=get_user_settings(SettingsVar.KUBERNETES_NAMESPACE), body=job
    )


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
