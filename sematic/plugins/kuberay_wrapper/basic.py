# Standard Library
from copy import deepcopy
from typing import Any, Dict, Union

# Sematic
from sematic.abstract_plugin import AbstractPluginSettingsVar
from sematic.plugins.abstract_kuberay_wrapper import (
    AbstractKuberayWrapper,
    RayClusterConfig,
    RayClusterManifest,
    RayNodeConfig,
    ScalingGroup,
)
from sematic.utils.exceptions import UnsupportedError, UnsupportedVersionError


class BasicKuberaySettingsVar(AbstractPluginSettingsVar):
    RAY_GPU_NODE_SELECTOR = "RAY_GPU_NODE_SELECTOR"
    RAY_GPU_TOLERATIONS = "RAY_GPU_TOLERATIONS"
    RAY_GPU_RESOURCE_REQUEST_KEY = "RAY_GPU_RESOURCE_REQUEST_KEY"


class _NeedsOverride:
    """Non-encodable signal value to indicate a template value needs to be overridden."""

    pass


MIN_SUPPORTED_KUBERAY_VERSION = (0, 4, 0)


_WORKER_GROUP_TEMPLATE: Dict[str, Any] = {
    "replicas": _NeedsOverride,
    "minReplicas": _NeedsOverride,
    "maxReplicas": _NeedsOverride,
    "groupName": _NeedsOverride,
    "rayStartParams": {"block": "true"},
    "template": {
        "spec": {
            "containers": [
                {
                    "name": "ray-worker",
                    "image": _NeedsOverride,
                    "lifecycle": {
                        "preStop": {"exec": {"command": ["/bin/sh", "-c", "ray stop"]}}
                    },
                    "volumeMounts": [{"mountPath": "/tmp/ray", "name": "ray-logs"}],
                    "resources": {
                        "limits": _NeedsOverride,
                        "requests": _NeedsOverride,
                    },
                }
            ],
            "initContainers": [
                {
                    "name": "init",
                    "image": "busybox:1.28",
                    "command": [
                        "sh",
                        "-c",
                        "until nslookup "
                        "$RAY_IP."
                        "$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)"
                        ".svc.cluster.local; "
                        "do echo waiting for K8s Service $RAY_IP; sleep 2; done",
                    ],
                }
            ],
            "volumes": [{"name": "ray-logs", "emptyDir": {}}],
        }
    },
}

_MANIFEST_TEMPLATE: Dict[str, Any] = {
    "apiVersion": "ray.io/v1alpha1",
    "kind": "RayCluster",
    "metadata": {
        "labels": {"controller-tools.k8s.io": "1.0"},
        "name": _NeedsOverride,
    },
    "spec": {
        "rayVersion": _NeedsOverride,
        "headGroupSpec": {
            "serviceType": "ClusterIP",
            "rayStartParams": {"dashboard-host": "0.0.0.0", "block": "true"},
            "template": {
                "metadata": {"labels": {}},
                "spec": {
                    "containers": [
                        {
                            "name": "ray-head",
                            "image": _NeedsOverride,
                            "ports": [
                                {"containerPort": 6379, "name": "gcs"},
                                {"containerPort": 8265, "name": "dashboard"},
                                {"containerPort": 10001, "name": "client"},
                            ],
                            "lifecycle": {
                                "preStop": {
                                    "exec": {"command": ["/bin/sh", "-c", "ray stop"]}
                                }
                            },
                            "volumeMounts": [
                                {"mountPath": "/tmp/ray", "name": "ray-logs"}
                            ],
                            "resources": {
                                "limits": _NeedsOverride,
                                "requests": _NeedsOverride,
                            },
                        }
                    ],
                    "volumes": [{"name": "ray-logs", "emptyDir": {}}],
                },
            },
        },
        "workerGroupSpecs": _NeedsOverride,
    },
}


class BasicKuberayWrapper(AbstractKuberayWrapper):
    _manifest_template = _MANIFEST_TEMPLATE
    _worker_group_template = _WORKER_GROUP_TEMPLATE

    @classmethod
    def create_cluster_manifest(  # type: ignore
        cls,
        image_uri: str,
        cluster_name: str,
        cluster_config: RayClusterConfig,
        kuberay_version: str,
    ) -> RayClusterManifest:
        cls._check_kuberay_version(kuberay_version)
        cls._validate_cluster_config(cluster_config=cluster_config)
        manifest = deepcopy(cls._manifest_template)
        manifest["metadata"]["name"] = cluster_name
        manifest["spec"]["rayVersion"] = cluster_config.ray_version

        head_group_spec = cls._make_head_group_spec(
            image_uri, cluster_config.head_node, manifest["spec"]["headGroupSpec"]
        )
        manifest["spec"]["headGroupSpec"] = head_group_spec

        manifest["spec"]["workerGroupSpecs"] = [
            cls._make_worker_group_spec(image_uri, group, i)
            for i, group in enumerate(cluster_config.scaling_groups)
        ]

        return manifest

    @classmethod
    def _make_worker_group_spec(
        cls, image_uri: str, worker_group: ScalingGroup, group_index: int
    ):
        group_manifest = deepcopy(cls._worker_group_template)
        group_manifest["replicas"] = worker_group.min_workers
        group_manifest["minReplicas"] = worker_group.min_workers
        group_manifest["maxReplicas"] = worker_group.max_workers
        group_manifest["groupName"] = f"worker-group-{group_index}"
        group_manifest["template"]["spec"]["containers"][0]["image"] = image_uri
        group_manifest["template"]["spec"]["containers"][0]["resources"][
            "limits"
        ] = cls._limits_for_node(worker_group.worker_nodes)
        group_manifest["template"]["spec"]["containers"][0]["resources"][
            "requests"
        ] = cls._requests_for_node(worker_group.worker_nodes)

        return group_manifest

    @classmethod
    def _check_kuberay_version(cls, kuberay_version: str):
        int_tuple_version = tuple(
            int(v) for v in kuberay_version.replace("v", "").split(".")
        )
        if (
            len(int_tuple_version) != 3
            or int_tuple_version < MIN_SUPPORTED_KUBERAY_VERSION
        ):
            raise UnsupportedVersionError(
                f"Unsupported version of Kuberay: {kuberay_version}. "
                f"Min supported version: {MIN_SUPPORTED_KUBERAY_VERSION}."
            )

    @classmethod
    def _validate_cluster_config(cls, cluster_config: RayClusterConfig) -> None:
        cls._validate_ray_version(cluster_config.ray_version)
        cls._validate_gpu_config(cluster_config)

    @classmethod
    def _validate_gpu_config(cls, cluster_config: RayClusterConfig) -> None:
        requires_gpus = cluster_config.head_node.gpu_count != 0 or any(
            group.worker_nodes.gpu_count != 0 for group in cluster_config.scaling_groups
        )
        if requires_gpus:
            raise UnsupportedError(
                f"The Kuberay plugin {cls.__name__} does not support nodes with GPUs"
            )

    @classmethod
    def _validate_ray_version(cls, ray_version: str) -> None:
        pass

    @classmethod
    def _make_head_group_spec(
        cls,
        image_uri: str,
        node_config: RayNodeConfig,
        head_group_template: Dict[str, Any],
    ) -> Dict[str, Any]:
        head_group_template["template"]["spec"]["containers"][0]["image"] = image_uri
        head_group_template["template"]["spec"]["containers"][0]["resources"][
            "limits"
        ] = cls._limits_for_node(node_config)
        head_group_template["template"]["spec"]["containers"][0]["resources"][
            "requests"
        ] = cls._requests_for_node(node_config)

        return head_group_template

    @classmethod
    def _limits_for_node(cls, node_config: RayNodeConfig) -> Dict[str, Union[str, int]]:
        # The basic plugin always makes requests & limits the same
        return cls._requests_for_node(node_config)

    @classmethod
    def _requests_for_node(
        cls, node_config: RayNodeConfig
    ) -> Dict[str, Union[str, int]]:
        milli_cpu = int(1000 * node_config.cpu)
        memory_mb = int(1024 * node_config.memory_gb)
        return {
            "cpu": f"{milli_cpu}m",
            "memory": f"{memory_mb}M",
        }
