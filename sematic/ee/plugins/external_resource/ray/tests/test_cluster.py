# Standard Library
from unittest.mock import MagicMock, patch

# Third-party
import ray  # type: ignore
from kubernetes.client.rest import ApiException  # type: ignore

# Sematic
from sematic.calculator import func
from sematic.ee.plugins.external_resource.ray.cluster import RayCluster
from sematic.plugins.abstract_external_resource import (
    ManagedBy,
    ResourceState,
    ResourceStatus,
)
from sematic.plugins.abstract_kuberay_wrapper import RayNodeConfig, SimpleRayCluster
from sematic.tests.fixtures import environment_variables


class RayClusterClientsMocked(RayCluster):
    _apps_api_mock = MagicMock(name="apps_api")
    _cluster_api_mock = MagicMock(name="cluster_api")
    _k8s_core_client_mock = MagicMock(name="k8s_core_client")

    @classmethod
    def reset_mocks(cls):
        cls._apps_api_mock.reset_mock()
        cls._cluster_api_mock.reset_mock()

    @classmethod
    def _apps_api(cls):
        return cls._apps_api_mock

    @classmethod
    def _cluster_api(cls):
        return cls._cluster_api_mock

    @classmethod
    def _k8s_core_client(cls):
        return cls._k8s_core_client_mock


@ray.remote
def add_with_ray(a, b):
    return a + b


@func
def add(a: int, b: int) -> int:
    with RayCluster(
        config=SimpleRayCluster(
            n_nodes=1, node_config=RayNodeConfig(cpu=1, memory_gb=1)
        )
    ):
        result = ray.get([add_with_ray.remote(a, b)], timeout=30)[0]
    return result


def test_timeout():
    cluster = RayCluster(
        config=SimpleRayCluster(
            n_nodes=1, node_config=RayNodeConfig(cpu=1, memory_gb=1)
        ),
        activation_timeout_seconds=42,
    )
    assert cluster.get_activation_timeout_seconds() == 42


def test_local_cluster():
    result = add(1, 2).resolve(tracking=False)
    assert result == 3

    # ray should have been shutdown
    assert not ray.is_initialized()


def test_get_kuberay_version():
    RayClusterClientsMocked.reset_mocks()
    fake_namespace = "fake_namespace"
    cluster = RayClusterClientsMocked(
        config=SimpleRayCluster(
            n_nodes=1, node_config=RayNodeConfig(cpu=1, memory_gb=1)
        )
    )
    mock_api = cluster._apps_api()
    mock_deployment_response = MagicMock(name="mock_deployment_response")
    mock_api.read_namespaced_deployment.return_value = mock_deployment_response
    mock_deployment_response.status.ready_replicas = 0

    version, error = cluster._get_kuberay_version(fake_namespace)
    assert version is None
    assert error == (
        "Kuberay has no ready replicas. Please ask your cluster administrator "
        "to verify the health of Kuberay, and refer to Kuberay docs for "
        "troubleshooting: https://ray-project.github.io/kuberay/"
    )

    mock_deployment_response.status.ready_replicas = 1
    container1 = MagicMock()
    container2 = MagicMock()

    container1.name = "foo"
    container1.image = "foo:v1.2.3"
    container2.name = "kuberay-operator"
    container2.image = "bar:v2.3.4"

    mock_deployment_response.spec.template.spec.containers = [container1, container2]
    version, error = cluster._get_kuberay_version(fake_namespace)
    assert error is None
    assert version == "v2.3.4"

    mock_api.read_namespaced_deployment.side_effect = ApiException(status=404)
    version, error = cluster._get_kuberay_version(fake_namespace)
    assert version is None
    assert error == (
        "Kuberay does not appear to be installed in your Kubernetes "
        "cluster. Please ask your cluster administrator to install it "
        "in order to proceed."
    )


def test_continue_deactivation():
    RayClusterClientsMocked.reset_mocks()
    cluster_name = "a_cluster_name"
    namespace = "test"
    with environment_variables(dict(KUBERNETES_NAMESPACE=namespace)):
        cluster = RayClusterClientsMocked(
            config=SimpleRayCluster(
                n_nodes=1, node_config=RayNodeConfig(cpu=1, memory_gb=1)
            ),
            status=ResourceStatus(
                state=ResourceState.ACTIVE,
                message="fake message",
                managed_by=ManagedBy.SERVER,
            ),
            _cluster_name=cluster_name,
        )
        reason = "some reason for deactivating"
        cluster = cluster._continue_deactivation(reason)
        assert cluster.status.state == ResourceState.DEACTIVATING
        assert cluster.status.message == (
            f"Requested deletion of RayCluster with name "
            f"{cluster_name} because: {reason}"
        )
        cluster._cluster_api().delete.assert_called_with(
            cluster_name, namespace=namespace
        )

        cluster._cluster_api().delete.side_effect = ApiException(status=404)
        cluster = cluster._continue_deactivation(reason)
        assert cluster.status.state == ResourceState.DEACTIVATED
        assert cluster.status.message == (
            f"Ray cluster with name '{cluster_name}' deleted because: {reason}"
        )


@patch(f"{RayCluster.__module__}.get_run")
@patch(f"{RayCluster.__module__}.get_run_ids_for_resource")
def test_request_cluster(mock_get_run_ids, mock_get_run):
    RayClusterClientsMocked.reset_mocks()
    kuberay_version = "v0.4.0"
    container_image_uri = "my_container_image_uri"
    mock_get_run_ids.return_value = ["abc123"]
    mock_get_run.return_value = MagicMock(container_image_uri=container_image_uri)
    namespace = "test"

    original_cluster = RayClusterClientsMocked(
        config=SimpleRayCluster(
            n_nodes=1, node_config=RayNodeConfig(cpu=1, memory_gb=1)
        ),
        status=ResourceStatus(
            state=ResourceState.CREATED,
            message="fake message",
            managed_by=ManagedBy.SERVER,
        ),
    )
    cluster = original_cluster
    cluster_name = f"ray-{cluster.id}"
    cluster._cluster_api().create.return_value.metadata.name = cluster_name
    cluster = cluster._request_cluster(kuberay_version, namespace)

    cluster._cluster_api().create.assert_called()
    assert cluster.status.state == ResourceState.ACTIVATING
    manifest = cluster._cluster_api().create.call_args[0][0]
    assert manifest["metadata"]["name"] == cluster_name

    RayClusterClientsMocked.reset_mocks()
    cluster = original_cluster
    cluster._cluster_api().create.side_effect = ApiException(status=500)
    cluster = cluster._request_cluster(kuberay_version, namespace)
    assert cluster.status.state == ResourceState.DEACTIVATING
    assert (
        f"Deactivating cluster because: Unable to request "
        f"RayCluster with name {cluster_name}: (500)"
    ) in cluster.status.message


def test_update_from_activating():
    RayClusterClientsMocked.reset_mocks()

    cluster_name = "cluster-name"
    cluster = RayClusterClientsMocked(
        config=SimpleRayCluster(
            n_nodes=3, node_config=RayNodeConfig(cpu=1, memory_gb=1)
        ),
        status=ResourceStatus(
            state=ResourceState.ACTIVATING,
            message="fake message",
            managed_by=ManagedBy.SERVER,
        ),
        _cluster_name=cluster_name,
    )

    namespace = "test"
    with environment_variables(dict(KUBERNETES_NAMESPACE=namespace)):
        cluster = cluster._update_from_activating()

    assert cluster.status.message == (
        "Ray cluster has 0 ready workers (counting the head) out of minimum 3."
    )
    assert cluster.status.state == ResourceState.ACTIVATING

    mock_head = MagicMock(name="mock-head")
    mock_head.status.phase = "Running"
    mock_head.status.container_statuses = [
        MagicMock(ready=True),
    ]

    mock_worker0 = MagicMock(name="mock-worker-0")
    mock_worker0.status.phase = "Running"
    mock_worker0.status.container_statuses = [
        MagicMock(ready=True),
    ]

    mock_worker1 = MagicMock(name="mock-worker-1")
    mock_worker1.status.phase = "Pending"
    mock_worker1.status.container_statuses = [
        MagicMock(ready=False),
    ]

    cluster._k8s_core_client().list_namespaced_pod.return_value = MagicMock(
        name="pod_list",
        items=[
            mock_head,
            mock_worker0,
            mock_worker1,
        ],
    )

    with environment_variables(dict(KUBERNETES_NAMESPACE=namespace)):
        cluster = cluster._update_from_activating()

    assert cluster.status.message == (
        "Ray cluster has 2 ready workers (counting the head) out of minimum 3."
    )
    assert cluster.status.state == ResourceState.ACTIVATING

    # try just moving to running--shouldn't change since pod is not ready yet
    mock_worker1.status.phase = "Running"
    with environment_variables(dict(KUBERNETES_NAMESPACE=namespace)):
        cluster = cluster._update_from_activating()

    assert cluster.status.message == (
        "Ray cluster has 2 ready workers (counting the head) out of minimum 3."
    )
    assert cluster.status.state == ResourceState.ACTIVATING

    # make final pod ready
    mock_worker1.status.container_statuses = [
        MagicMock(ready=True),
    ]
    with environment_variables(dict(KUBERNETES_NAMESPACE=namespace)):
        cluster = cluster._update_from_activating()

    assert cluster.status.message == ("Ready to use remote Ray cluster.")
    assert cluster.status.state == ResourceState.ACTIVE
