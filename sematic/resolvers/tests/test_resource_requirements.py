# Third-party
import pytest

# Sematic
from sematic.resolvers.resource_requirements import (
    KubernetesCapabilities,
    KubernetesHostPathMount,
    KubernetesResourceRequirements,
    KubernetesSecretMount,
    KubernetesSecurityContext,
    KubernetesToleration,
    KubernetesTolerationEffect,
    KubernetesTolerationOperator,
    ResourceRequirements,
)
from sematic.types.serialization import (
    value_from_json_encodable,
    value_to_json_encodable,
)


def test_is_serializable():
    requirements = ResourceRequirements(
        kubernetes=KubernetesResourceRequirements(
            node_selector={"foo": "bar"},
            requests={"cpu": "500m", "memory": "100Gi"},
            secret_mounts=KubernetesSecretMount(
                environment_secrets={"a": "b"},
                file_secret_root_path="/foo/bar",
                file_secrets={"c": "d"},
            ),
            tolerations=[
                KubernetesToleration(
                    key="k",
                    value="v",
                    effect=KubernetesTolerationEffect.NoExecute,
                    operator=KubernetesTolerationOperator.Equal,
                    toleration_seconds=42,
                )
            ],
            mount_expanded_shared_memory=True,
            security_context=KubernetesSecurityContext(
                privileged=True,
                allow_privilege_escalation=True,
                capabilities=KubernetesCapabilities(add=["SYS_ADMIN"]),
            ),
            host_path_mounts=[
                KubernetesHostPathMount(
                    name="volume-tmp",
                    node_path="/tmp",
                    pod_mount_path="/host_tmp",
                    type="Directory",
                ),
            ],
        )
    )
    encoded = value_to_json_encodable(requirements, ResourceRequirements)
    decoded = value_from_json_encodable(encoded, ResourceRequirements)
    assert decoded == requirements


def test_tolerations_validation():
    with pytest.raises(
        ValueError,
        match="toleration_seconds should only be specified when the effect is NoExecute.",
    ):
        KubernetesToleration(
            key="k",
            value="v",
            effect=KubernetesTolerationEffect.PreferNoSchedule,
            operator=KubernetesTolerationOperator.Equal,
            toleration_seconds=42,
        )


def test_host_path_mounts_name_sanitization():
    mount = KubernetesHostPathMount(node_path="/tmp", pod_mount_path="/host_tmp")
    assert mount.name == "volume-host-tmp"

    mount = KubernetesHostPathMount(name="", node_path="/tmp", pod_mount_path="/host_tmp")
    assert mount.name == "volume-host-tmp"

    path = "/0123456789012345678901234567890123456789012345678901234567890123456789"
    mount = KubernetesHostPathMount(node_path="/tmp", pod_mount_path=path)
    assert len(mount.name) == 64
    assert mount.name[:58] == "volume-012345678901234567890123456789012345678901234567890"
