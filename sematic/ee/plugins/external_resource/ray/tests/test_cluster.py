# Third-party
import ray  # type: ignore

# Sematic
from sematic.calculator import func
from sematic.ee.plugins.external_resource.ray.cluster import RayCluster
from sematic.plugins.abstract_kuberay_wrapper import RayNodeConfig, SimpleRayCluster


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


def test_local_cluster():
    result = add(1, 2).resolve(tracking=False)
    assert result == 3

    # ray should have been shutdown
    assert not ray.is_initialized()
