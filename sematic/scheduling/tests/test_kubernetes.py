# Standard Library
from datetime import datetime
from unittest import mock

# Third-party
import pytest
from kubernetes.client.exceptions import ApiException

# Sematic
from sematic.api.tests.fixtures import mock_server_settings
from sematic.config.server_settings import ServerSettingsVar
from sematic.db.tests.fixtures import make_job
from sematic.resolvers.resource_requirements import (
    KubernetesResourceRequirements,
    KubernetesSecretMount,
    KubernetesToleration,
    KubernetesTolerationEffect,
    KubernetesTolerationOperator,
    ResourceRequirements,
)
from sematic.scheduling.job_details import (
    JobDetails,
    KubernetesJobCondition,
    PodSummary,
)
from sematic.scheduling.kubernetes import (
    _schedule_kubernetes_job,
    cancel_job,
    refresh_job,
    schedule_run_job,
)
from sematic.tests.fixtures import environment_variables  # noqa: F401


@mock.patch("sematic.scheduling.kubernetes.load_kube_config")
@mock.patch("sematic.scheduling.kubernetes.kubernetes.client.BatchV1Api")
def test_cancel_job(k8s_batch_client: mock.MagicMock, mock_kube_config):
    job = make_job(
        run_id="abc",
        name="some-name",
        namespace="some-namespace",
    )
    cancel_job(job)
    k8s_batch_client.return_value.delete_namespaced_job.assert_called_once_with(
        namespace=job.namespace,
        name=job.name,
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
    custom_service_account = "custom-sa"
    args = ["a", "b", "c"]
    configured_env_vars = {
        "SOME_ENV_VAR": "some-env-var-value",
        "SEMATIC_API_ADDRESS": "http://theurl.com",
    }
    api_url_override = "http://urloverride.com"

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
            mount_expanded_shared_memory=True,
        )
    )

    with environment_variables({"SEMATIC_CONTAINER_IMAGE": image_uri}):
        _schedule_kubernetes_job(
            name=name,
            image=image_uri,
            environment_vars=configured_env_vars,
            namespace=namespace,
            service_account=custom_service_account,
            resource_requirements=resource_requirements,
            api_address_override=api_url_override,
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
    assert job.spec.template.spec.service_account_name == custom_service_account

    shared_memory_volume = job.spec.template.spec.volumes[1]
    assert shared_memory_volume.name == "expanded-shared-memory-volume"
    assert shared_memory_volume.empty_dir.medium == "Memory"

    container = job.spec.template.spec.containers[0]
    assert container.args == args
    env_vars = container.env
    secret_env_var = next(
        var for var in env_vars if var.name == next(iter(environment_secrets.values()))
    )
    assert secret_env_var.value_from.secret_key_ref.key == next(
        iter(environment_secrets)
    )

    final_api_url_var = next(
        var.value for var in env_vars if var.name == "SEMATIC_API_ADDRESS"
    )
    assert final_api_url_var == api_url_override

    del configured_env_vars["SEMATIC_API_ADDRESS"]
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
        JobDetails(
            try_number=0,
            pending_or_running_pod_count=0,
            succeeded_pod_count=0,
            has_started=False,
            still_exists=True,
            start_time=0.0,
            has_infra_failure=False,
            current_pods=[
                PodSummary(
                    pod_name="foo",
                    container_restart_count=0,
                    phase="Running",
                    condition_message=None,
                    condition=None,
                    unschedulable_message=None,
                    container_condition_message=None,
                    container_exit_code=None,
                    start_time_epoch_seconds=None,
                    node_name=None,
                    has_infra_failure=False,
                ),
            ],
        ),
        True,  # job hasn't started yet
    ),
    (
        JobDetails(
            try_number=0,
            pending_or_running_pod_count=1,
            succeeded_pod_count=0,
            has_started=True,
            still_exists=True,
            start_time=datetime.now().timestamp(),
            has_infra_failure=False,
            current_pods=[
                PodSummary(
                    pod_name="foo",
                    container_restart_count=0,
                    phase="Pending",
                    condition_message="Pod condition is 'Initialized'",
                    condition=None,
                    unschedulable_message=None,
                    container_condition_message="Container is waiting: ContainerCreating",
                    container_exit_code=None,
                    start_time_epoch_seconds=None,
                    node_name="foo-node",
                    has_infra_failure=False,
                ),
            ],
        ),
        True,  # job has started and has pending pods
    ),
    (
        JobDetails(
            try_number=0,
            pending_or_running_pod_count=1,
            succeeded_pod_count=0,
            has_started=True,
            still_exists=True,
            start_time=datetime.now().timestamp(),
            has_infra_failure=False,
            current_pods=[
                PodSummary(
                    pod_name="foo",
                    container_restart_count=0,
                    phase="Pending",
                    condition_message=(
                        "Pod condition is NOT 'PodScheduled': Unschedulable; "
                        "0/2 nodes are available: "
                        "1 Insufficient cpu, "
                        "1 Insufficient memory, "
                        "1 node(s) didn't match Pod's node affinity/selector."
                    ),
                    condition=None,
                    unschedulable_message=(
                        "0/2 nodes are available: "
                        "1 Insufficient cpu, "
                        "1 Insufficient memory, "
                        "1 node(s) didn't match Pod's node affinity/selector."
                    ),
                    container_condition_message=None,
                    container_exit_code=None,
                    start_time_epoch_seconds=None,
                    node_name="foo-node",
                    has_infra_failure=False,
                ),
            ],
        ),
        True,  # job has started and has unschedulable pods
    ),
    (
        JobDetails(
            try_number=0,
            pending_or_running_pod_count=1,
            succeeded_pod_count=0,
            has_started=True,
            still_exists=True,
            start_time=datetime.now().timestamp(),
            has_infra_failure=False,
            current_pods=[
                PodSummary(
                    pod_name="foo",
                    container_restart_count=0,
                    phase="Running",
                    condition_message=("Pod condition is 'Ready'"),
                    condition="Ready",
                    unschedulable_message=None,
                    container_condition_message="Container is running",
                    container_exit_code=None,
                    start_time_epoch_seconds=None,
                    node_name="foo-node",
                    has_infra_failure=False,
                ),
            ],
        ),
        True,  # job has started and has active pods
    ),
    (
        JobDetails(
            try_number=0,
            pending_or_running_pod_count=0,
            succeeded_pod_count=1,
            has_started=True,
            still_exists=True,
            start_time=datetime.now().timestamp(),
            has_infra_failure=False,
            current_pods=[
                PodSummary(
                    pod_name="foo",
                    container_restart_count=0,
                    phase="Succeeded",
                    condition_message=("Pod condition is 'Ready'"),
                    condition="Ready",
                    unschedulable_message=None,
                    container_condition_message="Container is running",
                    container_exit_code=0,
                    start_time_epoch_seconds=None,
                    node_name="foo-node",
                    has_infra_failure=False,
                ),
            ],
        ),
        False,  # job has completed successfully
    ),
    (
        JobDetails(
            try_number=0,
            pending_or_running_pod_count=0,
            succeeded_pod_count=0,
            has_started=True,
            still_exists=True,
            start_time=datetime.now().timestamp(),
            has_infra_failure=False,
            current_pods=[
                PodSummary(
                    pod_name="foo",
                    container_restart_count=0,
                    phase="Failed",
                    condition_message=("Pod condition is 'Initialized'"),
                    condition="Failed",
                    unschedulable_message=None,
                    container_condition_message="Container is terminated: OOMKilled",
                    container_exit_code=0,
                    start_time_epoch_seconds=None,
                    node_name="foo-node",
                    has_infra_failure=True,
                ),
            ],
        ),
        False,  # job has failed
    ),
    (
        JobDetails(
            try_number=0,
            pending_or_running_pod_count=0,
            succeeded_pod_count=1,
            has_started=True,
            still_exists=False,
            start_time=datetime.now().timestamp(),
            has_infra_failure=False,
            current_pods=[],
        ),
        False,  # job completed long ago and no longer exists
    ),
    (
        JobDetails(
            try_number=0,
            pending_or_running_pod_count=1,
            succeeded_pod_count=0,
            has_started=True,
            still_exists=False,
            start_time=datetime.now().timestamp(),
            has_infra_failure=False,
            current_pods=[],
        ),
        False,  # job was not updated between start and complete disappearance
    ),
]


@pytest.mark.parametrize(
    "job_details, expected",
    IS_ACTIVE_CASES,
)
def test_job_is_active(job_details, expected):
    assert job_details.get_status(0).is_active() == expected


@mock.patch("sematic.scheduling.kubernetes.load_kube_config")
@mock.patch("sematic.scheduling.kubernetes.kubernetes.client.BatchV1Api")
def test_refresh_job(mock_batch_api, mock_load_kube_config):
    mock_k8s_job = mock.MagicMock()
    mock_batch_api.return_value.read_namespaced_job_status.return_value = mock_k8s_job
    name = "the-name"
    namespace = "the-namespace"
    job = make_job(
        name=name,
        namespace=namespace,
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

    assert job.details.has_started
    assert job.details.pending_or_running_pod_count == 1
    assert job.details.still_exists

    mock_batch_api.return_value.read_namespaced_job_status.side_effect = ApiException()
    mock_batch_api.return_value.read_namespaced_job_status.side_effect.status = 404
    job = refresh_job(job)
    assert not job.details.still_exists


# kubernetes.client.CoreV1Api().list_namespaced_pod
@mock.patch("sematic.scheduling.kubernetes.load_kube_config")
@mock.patch("sematic.scheduling.kubernetes.kubernetes.client.CoreV1Api")
@mock.patch("sematic.scheduling.kubernetes.kubernetes.client.BatchV1Api")
def test_refresh_job_single_condition(
    mock_batch_api, mock_core_api, mock_load_kube_config
):
    mock_k8s_job = mock.MagicMock(name="mock-k8s-job")
    mock_batch_api.return_value.read_namespaced_job_status.return_value = mock_k8s_job

    mock_pod = mock.MagicMock(name="mock-pod")
    mock_list_pod_response = mock.MagicMock(name="mock-list-response")
    mock_list_pod_response.items = [mock_pod]
    mock_core_api.return_value.list_namespaced_pod.return_value = mock_list_pod_response

    namespace = "the-namespace"
    name = "the-name"
    job = make_job(name=name, namespace=namespace)
    mock_k8s_job.status.active = 1
    mock_k8s_job.status.succeeded = 0

    fail_condition = mock.MagicMock()
    fail_condition.status = "True"
    fail_condition.type = KubernetesJobCondition.Failed.value
    fail_condition.lastTransitionTime = 1
    mock_k8s_job.status.conditions = [
        fail_condition,
    ]
    mock_pod.status.conditions = [fail_condition]
    mock_pod.status.phase = "Running"

    job = refresh_job(job)

    assert job.details.has_started
    assert job.details.pending_or_running_pod_count == 1
    assert job.details.current_pods[0].condition == KubernetesJobCondition.Failed.value
    assert job.details.still_exists

    mock_batch_api.return_value.read_namespaced_job_status.side_effect = ApiException()
    mock_batch_api.return_value.read_namespaced_job_status.side_effect.status = 404
    job = refresh_job(job)
    assert not job.details.still_exists


@mock.patch("sematic.scheduling.kubernetes._schedule_kubernetes_job")
@mock.patch("sematic.scheduling.kubernetes._unique_job_id_suffix", return_value="foo")
def test_schedule_run_job(mock_uuid, mock_schedule_k8s_job):

    settings = {"SOME_SETTING": "SOME_VALUE"}
    resource_requests = ResourceRequirements(
        kubernetes=KubernetesResourceRequirements(),
    )
    image = "the_image"
    run_id = "run_id"
    namespace = "the-namespace"
    custom_service_account = "custom-sa"
    custom_api_address = "http://customurl.com"
    custom_socketio_address = "http//customurl-socketio.com"

    server_settings = {
        ServerSettingsVar.KUBERNETES_NAMESPACE: namespace,
        ServerSettingsVar.SEMATIC_WORKER_KUBERNETES_SA: custom_service_account,
        ServerSettingsVar.SEMATIC_WORKER_API_ADDRESS: custom_api_address,
        ServerSettingsVar.SEMATIC_WORKER_SOCKET_IO_ADDRESS: custom_socketio_address,
    }

    with mock_server_settings(server_settings):
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
        service_account=custom_service_account,
        api_address_override=custom_api_address,
        socketio_address_override=custom_socketio_address,
        resource_requirements=resource_requests,
        args=["--run_id", run_id],
    )
