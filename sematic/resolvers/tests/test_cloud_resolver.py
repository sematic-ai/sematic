# Standard Library
from unittest import mock

# Sematic
import sematic.api_client as api_client
from sematic.api.tests.fixtures import (  # noqa: F401
    mock_no_auth,
    mock_requests,
    test_client,
)
from sematic.calculator import func
from sematic.db.models.resolution import ResolutionStatus
from sematic.db.tests.fixtures import test_db  # noqa: F401
from sematic.resolvers.cloud_resolver import CloudResolver, _schedule_job
from sematic.resolvers.resource_requirements import (
    KUBERNETES_SECRET_NAME,
    KubernetesResourceRequirements,
    KubernetesSecretMount,
    ResourceRequirements,
)
from sematic.tests.fixtures import (  # noqa: F401
    environment_variables,
    test_storage,
    valid_client_version,
)


@func
def add(a: float, b: float) -> float:
    return a + b


# TODO: support pipeline args
@func
def pipeline() -> float:
    return add(1, 2)


@mock.patch("sematic.resolvers.cloud_resolver.get_image_uri")
@mock.patch("sematic.resolvers.cloud_resolver._schedule_job")
@mock.patch("kubernetes.config.load_kube_config")
@mock_no_auth
def test_simulate_cloud_exec(
    mock_load_kube_config: mock.MagicMock,
    mock_schedule_job: mock.MagicMock,
    mock_get_image: mock.MagicMock,
    mock_requests,  # noqa: F811
    test_db,  # noqa: F811
    test_storage,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    # On the user's machine
    mock_get_image.return_value = "some_image"

    resolver = CloudResolver(detach=True)

    future = pipeline()

    result = future.resolve(resolver)

    assert result == future.id

    mock_schedule_job.assert_called_once_with(
        future.id, "sematic-driver-{}".format(future.id), resolve=True
    )
    mock_load_kube_config.assert_called_once()
    # In the driver job

    runs, artifacts, edges = api_client.get_graph(future.id)

    driver_resolver = CloudResolver(detach=False, is_running_remotely=True)

    driver_resolver.set_graph(runs=runs, artifacts=artifacts, edges=edges)
    assert (
        api_client.get_resolution(future.id).status == ResolutionStatus.SCHEDULED.value
    )
    output = driver_resolver.resolve(future)

    assert output == 3
    assert (
        api_client.get_resolution(future.id).status == ResolutionStatus.COMPLETE.value
    )


@mock.patch("sematic.resolvers.cloud_resolver.kubernetes.client.BatchV1Api")
@mock.patch("sematic.user_settings.get_all_user_settings")
def test_schedule_job(mock_user_settings, k8s_batch_client):
    run_id = "run_id"
    name = "the-name"
    requests = {"cpu": "42"}
    node_selector = {"foo": "bar"}
    environment_secrets = {"api_key_1": "MY_API_KEY"}
    file_secrets = {"api_key_2": "the_file.txt"}
    secret_root = "/the-secrets"
    image_uri = "the-image"
    namespace = "the-namespace"

    resource_requirements = ResourceRequirements(
        kubernetes=KubernetesResourceRequirements(
            requests=requests,
            node_selector=node_selector,
            secret_mounts=KubernetesSecretMount(
                environment_secrets=environment_secrets,
                file_secrets=file_secrets,
                file_secret_root_path=secret_root,
            ),
        )
    )
    mock_user_settings.return_value = {"KUBERNETES_NAMESPACE": namespace}
    with environment_variables({"SEMATIC_CONTAINER_IMAGE": image_uri}):
        _schedule_job(
            run_id=run_id, name=name, resource_requirements=resource_requirements
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
    assert container.args == ["--run_id", run_id]
    env_vars = container.env
    secret_env_var = next(
        var for var in env_vars if var.name == next(iter(environment_secrets.values()))
    )
    assert secret_env_var.value_from.secret_key_ref.key == next(
        iter(environment_secrets)
    )
    assert secret_env_var.value_from.secret_key_ref.name == KUBERNETES_SECRET_NAME
    assert container.image == image_uri
    assert container.resources.limits == requests
    assert container.resources.requests == requests
