# Third-party
import pytest

# Sematic
from sematic.resolvers.resource_requirements import (
    KubernetesResourceRequirements,
    KubernetesSecretMount,
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
        )
    )
    encoded = value_to_json_encodable(requirements, ResourceRequirements)
    decoded = value_from_json_encodable(encoded, ResourceRequirements)
    assert decoded == requirements


def test_validation():
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
