# Standard Library
import json
from dataclasses import replace

# Third-party
import pytest

# Sematic
from sematic.plugins.abstract_kuberay_wrapper import (
    RayClusterConfig,
    RayNodeConfig,
    ScalingGroup,
)
from sematic.plugins.kuberay_wrapper.standard import (
    StandardKuberaySettingsVar,
    StandardKuberayWrapper,
)
from sematic.tests.fixtures import environment_variables
from sematic.utils.exceptions import UnsupportedError, UnsupportedVersionError

_TEST_IMAGE_URI = "test_image_uri"
_TEST_CLUSTER_NAME = "test_cluster_name"
_TEST_KUBERAY_VERSION = "v0.4.0"
_TEST_RAY_VERSION = "v2.1.0"

_HEAD_NODE_ONLY_CONFIG = RayClusterConfig(
    head_node=RayNodeConfig(
        cpu=2,
        memory_gb=4,
    ),
    ray_version=_TEST_RAY_VERSION,
)

_SINGLE_WORKER_GROUP_CONFIG = RayClusterConfig(
    head_node=RayNodeConfig(
        cpu=2,
        memory_gb=4,
    ),
    scaling_groups=[
        ScalingGroup(
            worker_nodes=RayNodeConfig(
                cpu=4,
                memory_gb=2,
            ),
            min_workers=4,
            max_workers=8,
        )
    ],
    ray_version=_TEST_RAY_VERSION,
)

_MULTIPLE_WORKER_GROUP_CONFIG = RayClusterConfig(
    head_node=RayNodeConfig(
        cpu=2,
        memory_gb=4,
    ),
    scaling_groups=[
        ScalingGroup(
            worker_nodes=RayNodeConfig(
                cpu=1,
                memory_gb=2,
            ),
            min_workers=1,
            max_workers=1,
        ),
        ScalingGroup(
            worker_nodes=RayNodeConfig(
                cpu=2,
                memory_gb=2,
            ),
            min_workers=2,
            max_workers=2,
        ),
    ],
    ray_version=_TEST_RAY_VERSION,
)

_EXPECTED_HEAD_ONLY_MANIFEST = {
    "apiVersion": "ray.io/v1alpha1",
    "kind": "RayCluster",
    "metadata": {
        "labels": {"controller-tools.k8s.io": "1.0"},
        "name": _TEST_CLUSTER_NAME,
    },
    "spec": {
        "rayVersion": _TEST_RAY_VERSION,
        "headGroupSpec": {
            "serviceType": "ClusterIP",
            "rayStartParams": {"dashboard-host": "0.0.0.0", "block": "true"},
            "template": {
                "metadata": {"labels": {}},
                "spec": {
                    "containers": [
                        {
                            "name": "ray-head",
                            "image": _TEST_IMAGE_URI,
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
                                "limits": {"cpu": "2000m", "memory": "4096M"},
                                "requests": {"cpu": "2000m", "memory": "4096M"},
                            },
                        }
                    ],
                    "tolerations": [],
                    "nodeSelector": {},
                    "volumes": [{"name": "ray-logs", "emptyDir": {}}],
                },
            },
        },
        "workerGroupSpecs": [],
    },
}

_EXPECTED_SINGLE_WORKER_GROUP = {
    "replicas": 4,
    "minReplicas": 4,
    "maxReplicas": 8,
    "groupName": "worker-group-0",
    "rayStartParams": {"block": "true"},
    "template": {
        "spec": {
            "containers": [
                {
                    "name": "ray-worker",
                    "image": _TEST_IMAGE_URI,
                    "lifecycle": {
                        "preStop": {"exec": {"command": ["/bin/sh", "-c", "ray stop"]}}
                    },
                    "volumeMounts": [{"mountPath": "/tmp/ray", "name": "ray-logs"}],
                    "resources": {
                        "limits": {"cpu": "4000m", "memory": "2048M"},
                        "requests": {"cpu": "4000m", "memory": "2048M"},
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
            "tolerations": [],
            "nodeSelector": {},
            "volumes": [{"name": "ray-logs", "emptyDir": {}}],
        }
    },
}


def test_head_node_only_cluster():
    manifest = StandardKuberayWrapper.create_cluster_manifest(  # type: ignore
        image_uri=_TEST_IMAGE_URI,
        cluster_name=_TEST_CLUSTER_NAME,
        cluster_config=_HEAD_NODE_ONLY_CONFIG,
        kuberay_version=_TEST_KUBERAY_VERSION,
    )

    # completed manifest should be json encodable
    json.dumps(manifest)
    assert manifest == _EXPECTED_HEAD_ONLY_MANIFEST


def test_single_worker_cluster():
    manifest = StandardKuberayWrapper.create_cluster_manifest(  # type: ignore
        image_uri=_TEST_IMAGE_URI,
        cluster_name=_TEST_CLUSTER_NAME,
        cluster_config=_SINGLE_WORKER_GROUP_CONFIG,
        kuberay_version=_TEST_KUBERAY_VERSION,
    )

    # completed manifest should be json encodable
    json.dumps(manifest)
    worker_groups = manifest["spec"]["workerGroupSpecs"]
    assert len(worker_groups) == 1

    worker_manifest = worker_groups[0]
    assert worker_manifest == _EXPECTED_SINGLE_WORKER_GROUP


def test_multiple_worker_cluster():
    manifest = StandardKuberayWrapper.create_cluster_manifest(  # type: ignore
        image_uri=_TEST_IMAGE_URI,
        cluster_name=_TEST_CLUSTER_NAME,
        cluster_config=_MULTIPLE_WORKER_GROUP_CONFIG,
        kuberay_version=_TEST_KUBERAY_VERSION,
    )

    # completed manifest should be json encodable
    json.dumps(manifest)
    worker_groups = manifest["spec"]["workerGroupSpecs"]
    assert len(worker_groups) == len(_MULTIPLE_WORKER_GROUP_CONFIG.scaling_groups)

    names = {group["groupName"] for group in worker_groups}
    assert len(names) == len(worker_groups)

    cpus = [
        group["template"]["spec"]["containers"][0]["resources"]["requests"]["cpu"]
        for group in worker_groups
    ]
    assert cpus == ["1000m", "2000m"]


def test_unsupported_kuberay():
    with pytest.raises(UnsupportedVersionError):
        StandardKuberayWrapper.create_cluster_manifest(  # type: ignore
            image_uri=_TEST_IMAGE_URI,
            cluster_name=_TEST_CLUSTER_NAME,
            cluster_config=_MULTIPLE_WORKER_GROUP_CONFIG,
            kuberay_version="v0.3.0",
        )


def test_gpus_not_supported():
    with pytest.raises(UnsupportedError):
        StandardKuberayWrapper.create_cluster_manifest(  # type: ignore
            image_uri=_TEST_IMAGE_URI,
            cluster_name=_TEST_CLUSTER_NAME,
            cluster_config=replace(
                _MULTIPLE_WORKER_GROUP_CONFIG,
                head_node=replace(
                    _MULTIPLE_WORKER_GROUP_CONFIG.head_node,
                    gpu_count=1,
                ),
            ),
            kuberay_version=_TEST_KUBERAY_VERSION,
        )

    with pytest.raises(UnsupportedError):
        StandardKuberayWrapper.create_cluster_manifest(  # type: ignore
            image_uri=_TEST_IMAGE_URI,
            cluster_name=_TEST_CLUSTER_NAME,
            cluster_config=replace(
                _MULTIPLE_WORKER_GROUP_CONFIG,
                scaling_groups=[
                    replace(
                        _MULTIPLE_WORKER_GROUP_CONFIG.scaling_groups[0],
                        worker_nodes=replace(
                            _MULTIPLE_WORKER_GROUP_CONFIG.scaling_groups[
                                0
                            ].worker_nodes,
                            gpu_count=1,
                        ),
                    )
                ],
            ),
            kuberay_version=_TEST_KUBERAY_VERSION,
        )


def test_head_node_gpus():
    gpu_tolerations = [
        dict(
            key="nvidia.com/gpu",
            operator="Equal",
            value="true",
            effect="NoSchedule",
        )
    ]
    gpu_node_selector = {
        "nvidia.com/gpu": "true",
    }
    non_gpu_tolerations = [
        dict(
            key="foo",
            operator="Equal",
            value="bar",
            effect="NoSchedule",
        )
    ]
    non_gpu_node_selector = {
        "baz": "qux",
    }
    with environment_variables(
        {
            StandardKuberaySettingsVar.RAY_SUPPORTS_GPUS.value: "true",
            StandardKuberaySettingsVar.RAY_GPU_TOLERATIONS.value: json.dumps(
                gpu_tolerations
            ),
            StandardKuberaySettingsVar.RAY_GPU_NODE_SELECTOR.value: json.dumps(
                gpu_node_selector
            ),
            StandardKuberaySettingsVar.RAY_NON_GPU_TOLERATIONS.value: json.dumps(
                non_gpu_tolerations
            ),
            StandardKuberaySettingsVar.RAY_NON_GPU_NODE_SELECTOR.value: json.dumps(
                non_gpu_node_selector
            ),
        }
    ):
        manifest = StandardKuberayWrapper.create_cluster_manifest(  # type: ignore
            image_uri=_TEST_IMAGE_URI,
            cluster_name=_TEST_CLUSTER_NAME,
            cluster_config=replace(
                _MULTIPLE_WORKER_GROUP_CONFIG,
                head_node=replace(
                    _MULTIPLE_WORKER_GROUP_CONFIG.head_node,
                    gpu_count=1,
                ),
            ),
            kuberay_version=_TEST_KUBERAY_VERSION,
        )
    assert (
        manifest["spec"]["headGroupSpec"]["template"]["spec"]["nodeSelector"]
        == gpu_node_selector
    )
    assert (
        manifest["spec"]["headGroupSpec"]["template"]["spec"]["tolerations"]
        == gpu_tolerations
    )
    assert manifest["spec"]["headGroupSpec"]["template"]["spec"]["containers"][0][
        "resources"
    ]["requests"] == {"cpu": "2000m", "memory": "4096M"}
    assert (
        manifest["spec"]["workerGroupSpecs"][0]["template"]["spec"]["nodeSelector"]
        == non_gpu_node_selector
    )
    assert (
        manifest["spec"]["workerGroupSpecs"][0]["template"]["spec"]["tolerations"]
        == non_gpu_tolerations
    )


def test_worker_node_gpus():
    expected_tolerations = [
        dict(
            key="nvidia.com/gpu",
            operator="Equal",
            value="true",
            effect="NoSchedule",
        )
    ]
    expected_node_selector = {
        "nvidia.com/gpu": "true",
    }
    with environment_variables(
        {
            StandardKuberaySettingsVar.RAY_SUPPORTS_GPUS.value: "true",
            StandardKuberaySettingsVar.RAY_GPU_TOLERATIONS.value: json.dumps(
                expected_tolerations
            ),
            StandardKuberaySettingsVar.RAY_GPU_NODE_SELECTOR.value: json.dumps(
                expected_node_selector
            ),
            StandardKuberaySettingsVar.RAY_GPU_RESOURCE_REQUEST_KEY.value: json.dumps(
                "nvidia.com/gpu"
            ),
        }
    ):
        manifest = StandardKuberayWrapper.create_cluster_manifest(  # type: ignore
            image_uri=_TEST_IMAGE_URI,
            cluster_name=_TEST_CLUSTER_NAME,
            cluster_config=replace(
                _MULTIPLE_WORKER_GROUP_CONFIG,
                scaling_groups=[
                    replace(
                        _MULTIPLE_WORKER_GROUP_CONFIG.scaling_groups[0],
                        worker_nodes=replace(
                            _MULTIPLE_WORKER_GROUP_CONFIG.scaling_groups[
                                0
                            ].worker_nodes,
                            gpu_count=2,
                        ),
                    )
                ],
            ),
            kuberay_version=_TEST_KUBERAY_VERSION,
        )
    assert (
        manifest["spec"]["workerGroupSpecs"][0]["template"]["spec"]["nodeSelector"]
        == expected_node_selector
    )
    assert (
        manifest["spec"]["workerGroupSpecs"][0]["template"]["spec"]["tolerations"]
        == expected_tolerations
    )
    assert manifest["spec"]["workerGroupSpecs"][0]["template"]["spec"]["containers"][0][
        "resources"
    ]["requests"] == {"cpu": "1000m", "nvidia.com/gpu": 2, "memory": "2048M"}
