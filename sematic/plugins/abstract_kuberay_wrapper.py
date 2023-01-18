# Standard Library
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Sematic
from sematic.abstract_plugin import AbstractPlugin

# This should be the manifest that can be passed to the
# Kubernetes API for the RayCluster CRD here:
# https://github.com/ray-project/kuberay/blob/master/helm-chart/kuberay-operator/crds/ray.io_rayclusters.yaml
RayClusterManifest = Dict[str, Any]


@dataclass(frozen=True)
class RayNodeConfig:
    """Configuration for an individual Ray Head/Worker compute node.

    Custom implementations of AbstractKuberayWrapper that allow for
    more advanced configuration (e.g. selecting among multiple kinds
    of GPU) can subclass this class and add extra configuration fields.

    Attributes
    ----------
    cpu:
        Number of CPUs for each node (supports fractional CPUs).
    memory_gb:
        Gigabytes of memory for each node (supports fractional values).
    gpu_count:
        The number of GPUs to attach. Not all deployments support GPUs.
    """

    cpu: float
    memory_gb: float
    gpu_count: int = 0


@dataclass(frozen=True)
class ScalingGroup:
    """Configuration for a group of Ray workers that will scale as a unit.

    Attributes
    ----------
    worker_nodes:
        A description of the compute resources available for each node in the
        scaling group.
    min_workers:
        The minimum number of workers the scaling group can scale to. Must be
        non-negative.
    max_workers:
        The maximum number of workers the scaling group can scale to. Must be
        equal to or greater than min_workers. For a fixed-size scaling group,
        set this equal to min_workers.
    """

    worker_nodes: RayNodeConfig
    min_workers: int = 1
    max_workers: int = 1

    def __post_init__(self):
        if self.min_workers <= 0:
            raise ValueError("min_workers must be >= 1")
        if self.min_workers > self.max_workers:
            raise ValueError("max_workers must be >= min_workers")


def _get_ray_version() -> str:
    """Default factory for the field ray_version in RayClusterConfig."""
    try:
        # Third-party
        import ray  # type: ignore

        return ray.__version__
    except ImportError:
        raise ValueError(
            "If ray is not installed, a value must be provided for ray_version"
        )


@dataclass(frozen=True)
class RayClusterConfig:
    """Description of a Ray Cluster

    Attributes
    ----------
    head_node:
        The configuration for the head node
    scaling_groups:
        A list of scaling groups. Each scaling group may have different
        properties for the nodes in the group.
    ray_version:
        The version of Ray the cluster should use. This will be populated
        automatically to the version of Ray currently installed, if Ray
        is already installed
    """

    head_node: RayNodeConfig
    scaling_groups: List[ScalingGroup] = field(default_factory=list)
    ray_version: str = field(default_factory=_get_ray_version)


def SimpleRayCluster(
    n_nodes: int, node_config: RayNodeConfig, ray_version: Optional[str] = None
) -> RayClusterConfig:
    """Configuration for a RayCluster with a fixed number of identical compute nodes

    Parameters
    ----------
    n_nodes:
        The number of nodes in the cluster, including the head node
    node_config:
        The configuration for each node in the cluster
    ray_version:
        The version of Ray used by the cluster. Will be populated automatically
        if Ray is installed. Otherwise it must be explicitly configured.
    """
    if ray_version is None:
        ray_version = _get_ray_version()
    if n_nodes < 1:
        raise ValueError("There must be at least one node in the Ray Cluster")
    n_workers = n_nodes - 1
    scaling_groups = []
    if n_workers > 0:
        scaling_groups.append(
            ScalingGroup(
                worker_nodes=node_config,
                min_workers=n_workers,
                max_workers=n_workers,
            )
        )
    return RayClusterConfig(
        head_node=node_config,
        scaling_groups=scaling_groups,
        ray_version=ray_version,
    )


class AbstractKuberayWrapper(AbstractPlugin):
    """Plugin to convert between a RayClusterConfig & a k8s manifest for the cluster."""

    @staticmethod
    def get_author() -> str:
        return "github.com/sematic-ai"

    @staticmethod
    def get_version() -> Tuple[int, int, int]:
        return 0, 1, 0

    @classmethod
    def create_cluster_manifest(
        cls,
        image_uri: str,
        cluster_name: str,
        cluster_config: RayClusterConfig,
        kuberay_version: str,
    ) -> RayClusterManifest:
        """Create a kubernetes manifest for a Ray cluster.

        Parameters
        ----------
        image_uri:
            The docker image that should be used by the RayCluster
        cluster_name:
            The name that the RayCluster object should have
        cluster_config:
            Specifications on what the RayCluster should look like
        kuberay_version:
            A Sematic version tuple for the installed Kuberay

        Returns
        -------
        A json-encodable for the RayCluster kubernetes object described by this CRD:
        https://github.com/ray-project/kuberay/blob/master/helm-chart/kuberay-operator/crds/ray.io_rayclusters.yaml

        Raises
        ------
        UnsupportedVersionError:
            If the provided version of Kuberay is not one that's supported by this plugin.
        UnsupportedError:
            If GPUs are requested but the plugin doesn't support configuring for GPUs.
        """
        raise NotImplementedError(
            "Child classes should implement create_cluster_manifest"
        )
