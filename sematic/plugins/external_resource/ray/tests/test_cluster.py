from sematic.plugins.external_resource.ray.cluster import RayCluster, RayClusterConfig

def test_foo():
    version = RayCluster._get_kuberay_version()
    assert version is not None