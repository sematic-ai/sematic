# Third-party
import enum
import kubernetes

# Sematic
from sematic.abstract_future import AbstractFuture
from sematic.resolvers.local_resolver import LocalResolver


class CloudResolver(LocalResolver):
    def __init__(self, attach: bool = False):
        super().__init__()

        self._attach = attach

        # TODO: Replace this with a cloud storage engine
        self._store_artifacts = True

    def resolve(self, future: AbstractFuture) -> str:
        if self._attach:
            return super().resolve(future)

        self._enqueue_future(future)

        run = self._populate_graph(future)

        run.root_id = future.id

        self._save_graph()

        job_name = _make_job_name(future, JobType.driver)
        _schedule_job(future.id, job_name)
        # SUBMIT ORCHESTRATOR JOB

        return run.id

    def _schedule_future(self, future: AbstractFuture) -> None:
        if future.props.parallelize:
            job_name = _make_job_name(future, JobType.worker)
            _schedule_job(future.id, job_name)
        else:
            self._run_inline(future)


class JobType(enum.Enum):
    driver = "driver"
    worker = "worker"


def _make_job_name(future: AbstractFuture, job_type: JobType) -> str:
    job_name = "-".join(
        ("sematic", job_type.value, future.calculator.__name__, future.id)
    )
    return job_name


def _schedule_job(run_id: str, name: str, resolve: bool = False):
    args = ["python3", "worker.py", "--run-id", run_id]

    if resolve:
        args.append("--resolve")

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
                    node_selector={},
                    # service_account_name="sematic-sa",
                    containers=[
                        kubernetes.client.V1Container(  # type: ignore
                            name=name,
                            image="python:3.9-bullseye",
                            args=args,
                            env=[],
                            volume_mounts=[],
                            resources=None,
                        )
                    ],
                    volumes=[],
                    tolerations=[],
                    restart_policy="Never",
                    # termination_grace_period_seconds=TERMINATION_GRACE_PERIOD_IN_SECS,
                ),
            ),
            backoff_limit=0,  # num retries
            ttl_seconds_after_finished=4 * 24 * 3600,
        ),
    )

    kubernetes.config.load_kube_config()  # type: ignore

    kubernetes.client.BatchV1Api().create_namespaced_job(  # type: ignore
        namespace="default", body=job
    )
