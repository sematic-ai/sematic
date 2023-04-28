# Standard Library
import json
from copy import deepcopy
from typing import Any, Dict, Type, Union

# Sematic
from sematic.abstract_plugin import AbstractPluginSettingsVar
from sematic.config.server_settings import ServerSettingsVar, get_server_setting
from sematic.config.settings import get_plugin_setting
from sematic.plugins.abstract_kuberay_wrapper import (
    AbstractKuberayWrapper,
    AutoscalerConfig,
    RayClusterConfig,
    RayClusterManifest,
    RayNodeConfig,
    ScalingGroup,
)
from sematic.scheduling.kubernetes import DEFAULT_WORKER_SERVICE_ACCOUNT
from sematic.utils.exceptions import UnsupportedUsageError, UnsupportedVersionError


class StandardKuberaySettingsVar(AbstractPluginSettingsVar):
    """Settings for the Kubray wrapper.

    Attributes
    ----------
    RAY_GPU_NODE_SELECTOR:
        The Kubernetes node selector that will be used for Ray nodes
        that use GPUs. Value should be json encoded into a string.
    RAY_NON_GPU_NODE_SELECTOR:
        The Kubernetes node selector that will be used for Ray nodes
        that don't use GPUs. Value should be json encoded into a string.
    RAY_GPU_TOLERATIONS:
        The Kubernetes tolerations that will be used for Ray nodes
        that use GPUs. Value should be json encoded into a string.
    RAY_NON_GPU_TOLERATIONS:
        The Kubernetes tolerations that will be used for Ray nodes
        that don't use GPUs. Value should be json encoded into a string.
    RAY_GPU_RESOURCE_REQUEST_KEY:
        The key that will be used in the Kubernetes resource requests/
        limits fields to indicate how many GPUs are required for Ray
        head/worker nodes. If not specified, requests for more than one
        GPU will be denied. Value should be json encoded into a string.
    RAY_SUPPORTS_GPUS:
        Whether Ray heads/workers can be assigned to Kubernetes nodes with
        GPUs. Should be either set to "true" or "false".
    """

    RAY_GPU_NODE_SELECTOR = "RAY_GPU_NODE_SELECTOR"
    RAY_NON_GPU_NODE_SELECTOR = "RAY_NON_GPU_NODE_SELECTOR"
    RAY_GPU_TOLERATIONS = "RAY_GPU_TOLERATIONS"
    RAY_NON_GPU_TOLERATIONS = "RAY_NON_GPU_TOLERATIONS"
    RAY_GPU_RESOURCE_REQUEST_KEY = "RAY_GPU_RESOURCE_REQUEST_KEY"
    RAY_SUPPORTS_GPUS = "RAY_SUPPORTS_GPUS"


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
            "tolerations": _NeedsOverride,
            "serviceAccount": _NeedsOverride,
            "serviceAccountName": _NeedsOverride,
            "nodeSelector": _NeedsOverride,
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
        # leave autoscaling off unless required, as there is a sidecar
        # required when autoscaling is active and we don't want to add
        # it unless it's needed.
        "enableInTreeAutoscaling": False,
        "autoscalerOptions": {
            "env": [
                {
                    "name": "RAY_LOG_TO_STDERR",
                    "value": "1",
                },
            ],
            "resources": {
                "limits": {
                    "cpu": _NeedsOverride,
                    "memory": _NeedsOverride,
                },
                "requests": {
                    "cpu": _NeedsOverride,
                    "memory": _NeedsOverride,
                },
            },
        },
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
                            "env": [
                                {
                                    "name": "RAY_LOG_TO_STDERR",
                                    "value": "1",
                                },
                            ],
                        }
                    ],
                    "tolerations": _NeedsOverride,
                    "serviceAccount": _NeedsOverride,
                    "serviceAccountName": _NeedsOverride,
                    "nodeSelector": _NeedsOverride,
                    "volumes": [{"name": "ray-logs", "emptyDir": {}}],
                },
            },
        },
        "workerGroupSpecs": _NeedsOverride,
    },
}


class StandardKuberayWrapper(AbstractKuberayWrapper):
    """Implementation designed for conventional K8s setups and recent Kuberay versions

    This implementation is structured so as to be subclassed to customize specific
    behaviors if more complex setups are required (e.g. mounting custom volumes to
    Ray nodes, additional pod lifecycle hooks, resource requests differing from resource
    limits, etc.).

    It supports GPUs, but only if configured to do so (see StandardKuberaySettingsVar).
    """

    _manifest_template = _MANIFEST_TEMPLATE
    _worker_group_template = _WORKER_GROUP_TEMPLATE

    @classmethod
    def get_settings_vars(cls) -> Type[AbstractPluginSettingsVar]:
        return StandardKuberaySettingsVar

    @classmethod
    def create_cluster_manifest(  # type: ignore
        cls,
        image_uri: str,
        cluster_name: str,
        cluster_config: RayClusterConfig,
        kuberay_version: str,
    ) -> RayClusterManifest:
        cls._validate_kuberay_version(kuberay_version)
        cls._validate_cluster_config(cluster_config=cluster_config)
        manifest = deepcopy(cls._manifest_template)
        manifest["metadata"]["name"] = cluster_name
        manifest["spec"]["rayVersion"] = cluster_config.ray_version
        manifest["spec"][
            "enableInTreeAutoscaling"
        ] = cluster_config.requires_autoscale()

        autoscaler_config = AutoscalerConfig(
            cpu=0.5,
            memory_gb=1,
        )
        if cluster_config.autoscaler_config is not None:
            autoscaler_config = cluster_config.autoscaler_config

        manifest["spec"]["autoscalerOptions"]["resources"] = {
            "requests": cls._requests_for_node(autoscaler_config),
            "limits": cls._requests_for_node(autoscaler_config),
        }

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
        group_manifest["template"]["spec"]["nodeSelector"] = cls._get_node_selector(
            worker_group.worker_nodes
        )
        group_manifest["template"]["spec"]["tolerations"] = cls._get_tolerations(
            worker_group.worker_nodes
        )
        group_manifest["template"]["spec"]["serviceAccount"] = _get_service_account()
        group_manifest["template"]["spec"][
            "serviceAccountName"
        ] = _get_service_account()

        return group_manifest

    @classmethod
    def _validate_kuberay_version(cls, kuberay_version: str):
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
        supports_gpus = _get_setting(
            StandardKuberaySettingsVar.RAY_SUPPORTS_GPUS, False
        )
        if requires_gpus and not supports_gpus:
            raise UnsupportedUsageError(
                f"The Kuberay plugin {cls.__name__} is not configured "
                "to support nodes with GPUs"
            )

    @classmethod
    def _validate_ray_version(cls, ray_version: str) -> None:
        if not ray_version.replace("v", "").startswith("2"):
            raise UnsupportedVersionError(
                "Only ray versions 2.0 or higher are supported."
            )

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
        head_group_template["template"]["spec"][
            "nodeSelector"
        ] = cls._get_node_selector(node_config)
        head_group_template["template"]["spec"]["tolerations"] = cls._get_tolerations(
            node_config
        )
        head_group_template["template"]["spec"][
            "serviceAccount"
        ] = _get_service_account()
        head_group_template["template"]["spec"][
            "serviceAccountName"
        ] = _get_service_account()

        return head_group_template

    @classmethod
    def _get_node_selector(cls, node_config: RayNodeConfig) -> Dict[str, Any]:
        uses_gpus = node_config.gpu_count > 0
        setting = (
            StandardKuberaySettingsVar.RAY_GPU_NODE_SELECTOR
            if uses_gpus
            else StandardKuberaySettingsVar.RAY_NON_GPU_NODE_SELECTOR
        )

        node_selector = _get_setting(setting, {})

        return node_selector

    @classmethod
    def _get_tolerations(cls, node_config: RayNodeConfig) -> Dict[str, Any]:
        uses_gpus = node_config.gpu_count > 0
        setting = (
            StandardKuberaySettingsVar.RAY_GPU_TOLERATIONS
            if uses_gpus
            else StandardKuberaySettingsVar.RAY_NON_GPU_TOLERATIONS
        )
        tolerations = _get_setting(setting, [])
        return tolerations

    @classmethod
    def _limits_for_node(cls, node_config: RayNodeConfig) -> Dict[str, str]:
        # The standard plugin always makes requests & limits the same
        return cls._requests_for_node(node_config)

    @classmethod
    def _requests_for_node(
        cls, node_config: Union[RayNodeConfig, AutoscalerConfig]
    ) -> Dict[str, str]:
        gpu_requests = {}
        gpu_count = getattr(node_config, "gpu_count", 0)
        if gpu_count > 0:
            gpu_request_key = _get_setting(
                StandardKuberaySettingsVar.RAY_GPU_RESOURCE_REQUEST_KEY, None
            )
            if gpu_request_key is None:
                if gpu_count > 1:
                    raise UnsupportedUsageError(
                        "You are requesting more than one GPU per node, but the server "
                        "is not configured to support more than one GPU per node."
                    )
            else:
                gpu_requests[gpu_request_key] = gpu_count

        milli_cpu = int(1000 * node_config.cpu)
        memory_mb = int(1024 * node_config.memory_gb)
        requests = {
            "cpu": f"{milli_cpu}m",
            "memory": f"{memory_mb}Mi",
        }
        requests.update(gpu_requests)
        return requests

    @classmethod
    def head_uri(cls, manifest: RayClusterManifest) -> str:
        name = manifest["metadata"]["name"]
        return f"ray://{name}-head-svc:10001"


def _get_setting(setting, default):
    value = json.loads(get_plugin_setting(StandardKuberayWrapper, setting, "null"))
    if value is None:
        value = default
    return value


def _get_service_account() -> str:
    return get_server_setting(
        ServerSettingsVar.SEMATIC_WORKER_KUBERNETES_SA, DEFAULT_WORKER_SERVICE_ACCOUNT
    )
