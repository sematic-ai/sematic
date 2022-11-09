# Standard Library
from datetime import datetime
from unittest import mock

# Third-party
import pytest
from kubernetes.client.exceptions import ApiException

# Sematic
from sematic.resolvers.resource_requirements import (
    KubernetesResourceRequirements,
    KubernetesSecretMount,
    KubernetesToleration,
    KubernetesTolerationEffect,
    KubernetesTolerationOperator,
    ResourceRequirements,
)
from sematic.scheduling.kubernetes import (
    JobType,
    KubernetesExternalJob,
    KubernetesJobCondition,
    _schedule_kubernetes_job,
    cancel_job,
    refresh_job,
    schedule_run_job,
)
from sematic.tests.fixtures import environment_variables  # noqa: F401
from sematic.user_settings import SettingsVar


@mock.patch("sematic.scheduling.kubernetes.load_kube_config")
@mock.patch("sematic.scheduling.kubernetes.kubernetes.client.BatchV1Api")
def test_cancel_job(k8s_batch_client: mock.MagicMock, mock_kube_config):
    external_job = KubernetesExternalJob.new(
        job_type=JobType.driver,
        try_number=0,
        run_id="abc",
        namespace="some-namespace",
    )
    cancel_job(external_job)
    k8s_batch_client.return_value.delete_namespaced_job.assert_called_once_with(
        namespace="some-namespace",
        name=external_job.kubernetes_job_name,
        grace_period_seconds=0,
        propagation_policy="Background",
    )


@mock.patch("sematic.scheduling.kubernetes.load_kube_config")
@mock.patch("sematic.scheduling.kubernetes.kubernetes.client.BatchV1Api")
def test_schedule_kubernetes_job(k8s_batch_client, mock_kube_config):
    name = "the-name"
    requests = {"cpu": "42"}
    node_selector = {"foo": "bar"}
    environment_secrets = {"api_key_1": "MY_API_KEY"}
    file_secrets = {"api_key_2": "the_file.txt"}
    secret_root = "/the-secrets"
    image_uri = "the-image"
    namespace = "the-namespace"
    args = ["a", "b", "c"]
    configured_env_vars = {"SOME_ENV_VAR": "some-env-var-value"}

    resource_requirements = ResourceRequirements(
        kubernetes=KubernetesResourceRequirements(
            requests=requests,
            node_selector=node_selector,
            secret_mounts=KubernetesSecretMount(
                environment_secrets=environment_secrets,
                file_secrets=file_secrets,
                file_secret_root_path=secret_root,
            ),
            tolerations=[
                KubernetesToleration(
                    key="foo",
                    operator=KubernetesTolerationOperator.Equal,
                    effect=KubernetesTolerationEffect.NoExecute,
                    value="bar",
                    toleration_seconds=42,
                ),
                KubernetesToleration(),
            ],
        )
    )
    with environment_variables({"SEMATIC_CONTAINER_IMAGE": image_uri}):
        _schedule_kubernetes_job(
            name=name,
            image=image_uri,
            environment_vars=configured_env_vars,
            namespace=namespace,
            resource_requirements=resource_requirements,
            args=args,
        )

    k8s_batch_client.return_value.create_namespaced_job.assert_called_once()
    _, kwargs = k8s_batch_client.return_value.create_namespaced_job.call_args
    assert kwargs["namespace"] == namespace
    job = kwargs["body"]
    assert job.spec.template.spec.node_selector == node_selector
    secret_volume = job.spec.template.spec.volumes[0]
    assert secret_volume.name == "sematic-func-secrets-volume"
    assert secret_volume.secret.items[0].key == next(iter(file_secrets.keys()))
    assert secret_volume.secret.items[0].path == next(iter(file_secrets.values()))
    container = job.spec.template.spec.containers[0]
    assert container.args == args
    env_vars = container.env
    secret_env_var = next(
        var for var in env_vars if var.name == next(iter(environment_secrets.values()))
    )
    assert secret_env_var.value_from.secret_key_ref.key == next(
        iter(environment_secrets)
    )
    normal_env_var = next(
        var for var in env_vars if var.name == next(iter(configured_env_vars.keys()))
    )
    assert normal_env_var.value == next(iter(configured_env_vars.values()))
    assert container.image == image_uri
    assert container.resources.limits == requests
    assert container.resources.requests == requests

    tolerations = job.spec.template.spec.tolerations
    assert len(tolerations) == 2
    assert tolerations[0].key == "foo"
    assert tolerations[0].value == "bar"
    assert tolerations[0].effect == "NoExecute"
    assert tolerations[0].operator == "Equal"
    assert tolerations[0].toleration_seconds == 42

    assert tolerations[1].key is None
    assert tolerations[1].value is None
    assert tolerations[1].effect is None
    assert tolerations[1].operator == "Equal"
    assert tolerations[1].toleration_seconds is None


IS_ACTIVE_CASES = [
    (
        KubernetesExternalJob(
            kind="k8s",
            try_number=0,
            external_job_id=KubernetesExternalJob.make_external_job_id(
                "a", "b", JobType.worker
            ),
            pending_or_running_pod_count=0,
            succeeded_pod_count=0,
            has_started=False,
            still_exists=True,
            start_time=None,
            most_recent_condition=None,
            most_recent_pod_phase_message=None,
            most_recent_pod_condition_message=None,
            most_recent_container_condition_message=None,
            has_infra_failure=False,
        ),
        True,  # job hasn't started yet
    ),
    (
        KubernetesExternalJob(
            kind="k8s",
            try_number=0,
            external_job_id=KubernetesExternalJob.make_external_job_id(
                "a", "b", JobType.worker
            ),
            pending_or_running_pod_count=1,
            succeeded_pod_count=0,
            has_started=True,
            still_exists=True,
            start_time=datetime.now().timestamp(),
            most_recent_condition=None,
            most_recent_pod_phase_message="Pod phase is 'Pending'",
            most_recent_pod_condition_message="Pod condition is 'Initialized'",
            most_recent_container_condition_message=(
                "Container is waiting: ContainerCreating"
            ),
            has_infra_failure=False,
        ),
        True,  # job has started and has pending pods
    ),
    (
        KubernetesExternalJob(
            kind="k8s",
            try_number=0,
            external_job_id=KubernetesExternalJob.make_external_job_id(
                "a", "b", JobType.worker
            ),
            pending_or_running_pod_count=1,
            succeeded_pod_count=0,
            has_started=True,
            still_exists=True,
            start_time=datetime.now().timestamp(),
            most_recent_condition=None,
            most_recent_pod_phase_message="Pod phase is 'Pending'",
            most_recent_pod_condition_message=(
                "Pod condition is NOT 'PodScheduled': Unschedulable; "
                "0/2 nodes are available: "
                "1 Insufficient cpu, "
                "1 Insufficient memory, "
                "1 node(s) didn't match Pod's node affinity/selector."
            ),
            most_recent_container_condition_message=None,
            has_infra_failure=False,
        ),
        True,  # job has started and has unschedulable pods
    ),
    (
        KubernetesExternalJob(
            kind="k8s",
            try_number=0,
            external_job_id=KubernetesExternalJob.make_external_job_id(
                "a", "b", JobType.worker
            ),
            pending_or_running_pod_count=1,
            succeeded_pod_count=0,
            has_started=True,
            still_exists=True,
            start_time=datetime.now().timestamp(),
            most_recent_condition=None,
            most_recent_pod_phase_message="Pod phase is 'Running'",
            most_recent_pod_condition_message="Pod condition is 'Ready'",
            most_recent_container_condition_message="Container is running",
            has_infra_failure=False,
        ),
        True,  # job has started and has active pods
    ),
    (
        KubernetesExternalJob(
            kind="k8s",
            try_number=0,
            external_job_id=KubernetesExternalJob.make_external_job_id(
                "a", "b", JobType.worker
            ),
            pending_or_running_pod_count=0,
            succeeded_pod_count=1,
            has_started=True,
            still_exists=True,
            start_time=datetime.now().timestamp(),
            most_recent_condition=KubernetesJobCondition.Complete.value,
            # k8 reports the pods from our completed jobs ar running for a while
            # probably a race condition
            most_recent_pod_phase_message="Pod phase is 'Running'",
            most_recent_pod_condition_message="Pod condition is 'Ready'",
            most_recent_container_condition_message="...",
            has_infra_failure=False,
        ),
        False,  # job has completed successfully
    ),
    (
        KubernetesExternalJob(
            kind="k8s",
            try_number=0,
            external_job_id=KubernetesExternalJob.make_external_job_id(
                "a", "b", JobType.worker
            ),
            pending_or_running_pod_count=0,
            succeeded_pod_count=0,
            has_started=True,
            still_exists=True,
            start_time=datetime.now().timestamp(),
            most_recent_condition=KubernetesJobCondition.Failed.value,
            most_recent_pod_phase_message="Pod phase is 'Failed'",
            most_recent_pod_condition_message="Pod condition is 'Initialized'",
            most_recent_container_condition_message="Container is terminated: OOMKilled",
            has_infra_failure=True,
        ),
        False,  # job has failed
    ),
    (
        KubernetesExternalJob(
            kind="k8s",
            try_number=0,
            external_job_id=KubernetesExternalJob.make_external_job_id(
                "a", "b", JobType.worker
            ),
            pending_or_running_pod_count=0,
            succeeded_pod_count=1,
            has_started=True,
            still_exists=False,
            start_time=1.01,
            most_recent_condition=KubernetesJobCondition.Complete.value,
            most_recent_pod_phase_message="Pod phase is 'Succeeded'",
            most_recent_pod_condition_message="...",
            most_recent_container_condition_message="...",
            has_infra_failure=False,
        ),
        False,  # job completed long ago and no longer exists
    ),
    (
        KubernetesExternalJob(
            kind="k8s",
            try_number=0,
            external_job_id=KubernetesExternalJob.make_external_job_id(
                "a", "b", JobType.worker
            ),
            pending_or_running_pod_count=0,
            succeeded_pod_count=0,
            has_started=True,
            still_exists=False,
            start_time=1.01,
            most_recent_condition=None,
            most_recent_pod_phase_message=None,
            most_recent_pod_condition_message=None,
            most_recent_container_condition_message=None,
            has_infra_failure=False,
        ),
        False,  # job was not updated between start and complete disappearance
    ),
]


@pytest.mark.parametrize(
    "job, expected",
    IS_ACTIVE_CASES,
)
def test_job_is_active(job, expected):
    assert job.is_active() == expected


@mock.patch("sematic.scheduling.kubernetes.load_kube_config")
@mock.patch("sematic.scheduling.kubernetes.kubernetes.client.BatchV1Api")
def test_refresh_job(mock_batch_api, mock_load_kube_config):
    mock_k8s_job = mock.MagicMock()
    mock_batch_api.return_value.read_namespaced_job_status.return_value = mock_k8s_job
    run_id = "the-run-id"
    namespace = "the-namespace"
    job = KubernetesExternalJob(
        kind="k8s",
        try_number=0,
        external_job_id=KubernetesExternalJob.make_external_job_id(
            run_id, namespace, JobType.worker
        ),
        pending_or_running_pod_count=0,
        succeeded_pod_count=1,
        has_started=True,
        still_exists=True,
        start_time=1.01,
        most_recent_condition=None,
        most_recent_pod_phase_message=None,
        most_recent_pod_condition_message=None,
        most_recent_container_condition_message=None,
        has_infra_failure=False,
    )
    mock_k8s_job.status.active = 1

    # should be impossible (or at least highly unlikely) to have 1 active and
    # 1 succeeded, but perhaps it could happen if 1 pod was terminating due
    # to an eviction and another had already started and completed. Just testing
    # here that the data is pulled from the job properly
    mock_k8s_job.status.succeeded = 1

    success_condition = mock.MagicMock()
    success_condition.status = "True"
    success_condition.type = KubernetesJobCondition.Complete.value
    success_condition.last_transition_time = 1

    fail_condition = mock.MagicMock()
    # aka, the Failed condition does NOT apply. K8s doesn't really set
    # conditions like this AFAICT, but this is what the semantics of
    # the conditions is supposed to be.
    fail_condition.status = "False"
    fail_condition.type = KubernetesJobCondition.Failed.value
    fail_condition.last_transition_time = 2
    mock_k8s_job.status.conditions = [
        success_condition,
        fail_condition,
    ]
    job = refresh_job(job)

    assert job.has_started
    assert job.pending_or_running_pod_count == 1
    assert job.most_recent_condition == KubernetesJobCondition.Complete.value
    assert job.still_exists

    mock_batch_api.return_value.read_namespaced_job_status.side_effect = ApiException()
    mock_batch_api.return_value.read_namespaced_job_status.side_effect.status = 404
    job = refresh_job(job)
    assert not job.still_exists


@mock.patch("sematic.scheduling.kubernetes.load_kube_config")
@mock.patch("sematic.scheduling.kubernetes.kubernetes.client.BatchV1Api")
def test_refresh_job_single_condition(mock_batch_api, mock_load_kube_config):
    mock_k8s_job = mock.MagicMock()
    mock_batch_api.return_value.read_namespaced_job_status.return_value = mock_k8s_job
    run_id = "the-run-id"
    namespace = "the-namespace"
    job = KubernetesExternalJob(
        kind="k8s",
        try_number=0,
        external_job_id=KubernetesExternalJob.make_external_job_id(
            run_id, namespace, JobType.worker
        ),
        pending_or_running_pod_count=0,
        succeeded_pod_count=1,
        has_started=True,
        still_exists=True,
        start_time=1.01,
        most_recent_condition=None,
        most_recent_pod_phase_message=None,
        most_recent_pod_condition_message=None,
        most_recent_container_condition_message=None,
        has_infra_failure=False,
    )
    mock_k8s_job.status.active = 0
    mock_k8s_job.status.succeeded = 0

    fail_condition = mock.MagicMock()
    fail_condition.status = "True"
    fail_condition.type = KubernetesJobCondition.Failed.value
    fail_condition.lastTransitionTime = 1
    mock_k8s_job.status.conditions = [
        fail_condition,
    ]
    job = refresh_job(job)

    assert job.has_started
    assert job.pending_or_running_pod_count == 0
    assert job.most_recent_condition == KubernetesJobCondition.Failed.value
    assert job.still_exists

    mock_batch_api.return_value.read_namespaced_job_status.side_effect = ApiException()
    mock_batch_api.return_value.read_namespaced_job_status.side_effect.status = 404
    job = refresh_job(job)
    assert not job.still_exists


@mock.patch("sematic.user_settings.get_active_user_settings")
@mock.patch("sematic.scheduling.kubernetes._schedule_kubernetes_job")
@mock.patch("sematic.scheduling.kubernetes._unique_job_id_suffix", return_value="foo")
def test_schedule_run_job(mock_uuid, mock_schedule_k8s_job, mock_user_settings):
    settings = {"SOME_SETTING": "SOME_VALUE"}
    resource_requests = ResourceRequirements(
        kubernetes=KubernetesResourceRequirements(),
    )
    image = "the_image"
    run_id = "run_id"
    namespace = "the-namespace"
    mock_user_settings.return_value = {SettingsVar.KUBERNETES_NAMESPACE: namespace}
    schedule_run_job(
        run_id=run_id,
        image=image,
        user_settings=settings,
        resource_requirements=resource_requests,
        try_number=1,
    )
    mock_schedule_k8s_job.assert_called_with(
        name=f"sematic-worker-{run_id}-foo",
        image=image,
        environment_vars=settings,
        namespace=namespace,
        resource_requirements=resource_requests,
        args=["--run_id", run_id],
    )
