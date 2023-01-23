# Standard Library
from dataclasses import replace

# Sematic
from sematic.calculator import func
from sematic.plugins.abstract_external_resource import ManagedBy, ResourceState
from sematic.plugins.abstract_kuberay_wrapper import RayNodeConfig, SimpleRayCluster
from sematic.plugins.external_resource.ray.cluster import RayCluster


@func
def foo():
    version, err = RayCluster._get_kuberay_version("dev1")
    assert version is not None
    cluster = RayCluster(
        config=SimpleRayCluster(
            n_nodes=1, node_config=RayNodeConfig(cpu=1, memory_gb=1)
        )
    )
    cluster = replace(
        cluster,
        status=replace(cluster.status, managed_by=ManagedBy.SERVER),
    )
    uri = (
        "558717131297.dkr.ecr.us-west-2.amazonaws.com/sematic-dev@"
        "sha256:6f089f664f135fe62b9fac3ed0261c0a7b794ba518bc109f025e516555aa9791"
    )
    cluster = cluster._request_cluster(
        kuberay_version=version,
        namespace="dev1",
        image_uri=uri,
    )
    assert cluster.status.state == ResourceState.ACTIVATING

    while cluster.status.state != ResourceState.ACTIVE:
        cluster = cluster.update()
    cluster = cluster.deactivate()
    while cluster.status.state != ResourceState.DEACTIVATED:
        cluster = cluster.update()
    cluster._continue_deactivation("Done with test")
    print(cluster)


def test_foo():
    foo().resolve()
