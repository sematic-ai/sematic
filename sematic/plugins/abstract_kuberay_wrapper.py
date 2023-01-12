# Standard Library
from abc import ABC, abstractclassmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# This should be the manifest that can be passed to the
# Kubernetes API for the RayCluster CRD here:
# https://github.com/ray-project/kuberay/blob/master/helm-chart/kuberay-operator/crds/ray.io_rayclusters.yaml
RayClusterManifest = Dict[str, Any]


@dataclass(frozen=True)
class RayNodeConfig:
    cpu: float
    memory_gb: float
    gpu_count: int = 0
    gpu_kind: Optional[str] = None


@dataclass(frozen=True)
class ScalingGroup:
    """Configuration for a group of Ray workers that will scale as a unit"""

    worker_nodes: RayNodeConfig
    min_workers: int = 1
    max_workers: int = 1

    def __post_init__(self):
        if self.min_workers <= 0:
            raise ValueError("min_workers must be >= 1")
        if self.min_workers > self.max_workers:
            raise ValueError("max_workers must be >= min_workers")


def _get_ray_version() -> str:
    """Default factory for the field ray_version in RayClusterConfig"""
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
    head_node: RayNodeConfig
    scaling_groups: List[ScalingGroup] = field(default_factory=list)
    ray_version: str = field(default_factory=_get_ray_version)


class AbstractKuberayWrapper(ABC):
    @abstractclassmethod
    def create_cluster_manifest(
        cls,
        image_uri: str,
        cluster_name: str,
        cluster_config: RayClusterConfig,
        kuberay_version: str,
        ray_version: str,
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
            If the provided version of Kuberay is not one that's supported by this plugin
        """
        pass
