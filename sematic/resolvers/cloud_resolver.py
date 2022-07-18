# Standard library
import enum
import os
import __main__
import logging
from typing import Dict, List, Optional

# Third-party
import kubernetes
import cloudpickle

# Sematic
from sematic.abstract_future import AbstractFuture, FutureState
from sematic.db.models.artifact import Artifact
from sematic.db.models.edge import Edge
from sematic.db.models.factories import get_artifact_value
from sematic.db.models.run import Run
from sematic.resolvers.local_resolver import LocalResolver, make_edge_key
from sematic.resolvers.resource_requirements import ResourceRequirements
from sematic.user_settings import (
    SettingsVar,
    get_all_user_settings,
    get_user_settings,
)
import sematic.api_client as api_client
import sematic.storage as storage


logger = logging.getLogger(__name__)


class CloudResolver(LocalResolver):
    def __init__(self, detach: bool = True):
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

    def _detach_resolution(self, future: AbstractFuture) -> str:
        run = self._populate_run_and_artifacts(future)

        run.root_id = future.id

        self._save_graph()

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
            self._handle_future_failure(future, Exception("Run failed"))

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

            # for parent_future in self._find_parent_futures(future):
            #    parent_future.value = value
            #    parent_future.run_handle = api_client.set_run_output_artifact(
            #        parent_future.run_handle.id, value
            #    )

        self._update_future_with_value(future, value)

    def _get_output_artifact(self, run_id: str) -> Optional[Artifact]:
        return self._output_artifacts_by_run_id.get(run_id)

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

    image = _get_image()

    node_selector = {}
    if resource_requirements is not None:
        node_selector = resource_requirements.kubernetes.node_selector
        logger.debug("kubernetes node_selector %s", node_selector)

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
                                    name=_CONTAINER_IMAGE_ENV_VAR,
                                    value=image,
                                )
                            ]
                            + [
                                kubernetes.client.V1EnvVar(  # type: ignore
                                    name=name,
                                    value=value,
                                )
                                for name, value in get_all_user_settings().items()
                            ],
                            volume_mounts=[],
                            resources=None,
                        )
                    ],
                    volumes=[],
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


_CONTAINER_IMAGE_ENV_VAR = "SEMATIC_CONTAINER_IMAGE"


def _get_image() -> str:
    if _CONTAINER_IMAGE_ENV_VAR in os.environ:
        return os.environ[_CONTAINER_IMAGE_ENV_VAR]

    with open(
        "{}_push_at_build.uri".format(os.path.splitext(__main__.__file__)[0])
    ) as f:
        return f.read()
