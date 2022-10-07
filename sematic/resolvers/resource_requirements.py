# Standard Library
from dataclasses import dataclass, field
from enum import Enum, unique
from typing import Dict, List, Optional, Union

KUBERNETES_SECRET_NAME = "sematic-func-secrets"


@dataclass
class KubernetesSecretMount:
    """Information about how to expose Kubernetes secrets when running a Sematic func.

    This can be used to mount credentials that the func may need to execute. To use it
    in this manner:

    1. Create a Kubernetes secret containing the credentials you need. The secret MUST be
        named "sematic-func-secrets" Instructions for this can be found here:
        https://kubernetes.io/docs/concepts/configuration/secret/
        In the "data" field of the secret, you should have key value pairs for every
        secret value you wish to expose for Sematic functions. For example, you might
        have the key `my-api-key` and the value `mYSu93Rs3cretKey`
    2. For the Sematic func that requires access to the secret, list it either as an
        environment secret (the secret's value will be stored in an environment variable)
        or as a file secret (the secret's value will be stored in a file).

    Before using Kubernetes secrets to give this kind of credential access, be aware that
    using them will allow anybody who can execute Sematic funcs in your cluster access to
    the secrets.

    Attributes
    ----------
    environment_secrets:
        A dict whose keys are the same as the subset of keys from the
        "sematic-func-secret" that you want mounted for the func, and whose values are
        the name of the environment variable where it should be exposed
    file_secrets:
        A dict whose keys are the same as the subset of keys from the
        "sematic-func-secret" that you want mounted for the func, and whose values are
        the path to the file within the container where the secret should be exposed.
        These file paths should be RELATIVE paths, they will be taken as relative to
        file_secret_root_path.
    file_secret_root_path:
        File secrets must all be stored in the same directory. This gives the directory
        where they will be stored. The directory must be a new directory, or the contents
        of the existing directory will be overwritten.
    """

    environment_secrets: Dict[str, str] = field(default_factory=dict)
    file_secrets: Dict[str, str] = field(default_factory=dict)
    file_secret_root_path: str = "/secrets"


@unique
class KubernetesTolerationOperator(Enum):
    """The way that a toleration should be checked to see if it applies

    See Kubernetes documentation for more:
    https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/

    Options
    -------
    Equal:
        value must be specified, and must be equal for the toleration and the taint
        for the toleration to be considered to apply. In addition to this condition,
        the "effect" must be equal for the toleration and the taint for the toleration
        to be considered to apply.
    Exists:
        value is not required. If a taint with the given key exists on the node,
        the toleration is considered to apply. In addition to this condition,
        the "effect" must be equal for the toleration and the taint for the toleration
        to be considered to apply.
    """

    Equal = "Equal"
    Exists = "Exists"


@unique
class KubernetesTolerationEffect(Enum):
    """The effect that the toleration is meant to tolerate

    See Kubernetes documentation for more:
    https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/

    Options
    -------
    NoSchedule:
        The toleration indicates that the pod can run on the node even
        if it has specified a NoSchedule taint, assuming the rest of
        the toleration matches the taint.
    PreferNoSchedule:
        The toleration indicates that the pod can run on the node even
        if it has specified a PreferNoSchedule taint, assuming the rest
        of the toleration matches the taint.
    NoExecute:
        The pod will not be evicted from the node even if the node has
        specified a NoExecute taint, assuming the rest of the toleration
        matches the taint.
    All:
        The pod will not be evicted from the node even if the node has
        any kind of taint, assuming the rest of the toleration
        matches the taint.
    """

    NoSchedule = "NoSchedule"
    PreferNoSchedule = "PreferNoSchedule"
    NoExecute = "NoExecute"
    All = "All"


@dataclass
class KubernetesToleration:
    """Toleration for a node taint, enabling the pod for the function to run on the node

    See Kubernetes documentation for more:
    https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/

    Attributes
    ----------
    key:
        The key for the node taint intended to be tolerated. If empty, means
        to match all keys AND all values
    operator:
        The way to compare the key/value pair to the node taint's key/value pair
        to see if the toleration applies
    effect:
        The effect of the node taint the toleration is intended to tolerate.
        Leaving it empty means to tolerate all effects.
    value:
        If the operator is Equals, this value will be compared to the value
        on the node taint to see if this toleration applies.
    toleration_seconds:
        Only specified when effect is NoExecute (otherwise is an error). It
        specifies the amount of time the pod can continue executing on a node
        with a NoExecute taint
    """

    key: Optional[str] = None
    operator: KubernetesTolerationOperator = KubernetesTolerationOperator.Equal
    effect: KubernetesTolerationEffect = KubernetesTolerationEffect.All
    value: Optional[str] = None
    toleration_seconds: Optional[int] = None

    def to_api_keyword_args(self) -> Dict[str, Optional[Union[str, int]]]:
        """Convert to the format for kwargs the API python client API for tolerations"""
        effect: Optional[str] = self.effect.value
        if self.effect == KubernetesTolerationEffect.All:
            # the actual API makes "all" the default behavior with no other way to
            # specify
            effect = None
        operator = self.operator.value
        return dict(
            effect=effect,
            key=self.key,
            operator=operator,
            toleration_seconds=self.toleration_seconds,
            value=self.value,
        )

    def __post_init__(self):
        """Ensure that the values in the toleration are valid; raise otherwise

        Raises
        ------
        ValueError:
           If the values are not valid
        """
        if not (self.key is None or isinstance(self.key, str)):
            raise ValueError(f"key must be None or a string, got: {self.key}")
        if not isinstance(self.operator, KubernetesTolerationOperator):
            raise ValueError(
                f"operator must be a {KubernetesTolerationOperator}, got {self.operator}"
            )
        if not isinstance(self.effect, KubernetesTolerationEffect):
            raise ValueError(
                f"effect must be a {KubernetesTolerationEffect}, got {self.effect}"
            )
        if not (self.value is None or isinstance(self.value, str)):
            raise ValueError(f"value must be None or a string, got: {self.value}")
        if not (
            self.toleration_seconds is None or isinstance(self.toleration_seconds, int)
        ):
            raise ValueError(
                "toleration_seconds must be None or an "
                f"int, got: {self.toleration_seconds}"
            )
        if (
            self.toleration_seconds is not None
            and self.effect != KubernetesTolerationEffect.NoExecute
        ):
            raise ValueError(
                "toleration_seconds should only be specified when the effect "
                "is NoExecute."
            )


@dataclass
class KubernetesResourceRequirements:
    """Information on the Kubernetes resources required.

    Attributes
    ----------
    node_selector:
        The kind of Kubernetes node that the job must run on. More detail can
        be found here:
        https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/
        The value of this field will be used as the nodeSelector described there.
    requests:
        Requests for resources on a kubernetes pod. More detail can be found
        here:
        https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
        The values used here will apply to both the "requests" and the "limits" of the
        job.
    secret_mounts:
        Requests to take the contents of Kubernetes secrets and expose them as
        environment variables or files on disk when running in the cloud.
    tolerations:
        If your Kubernetes configuration uses node taints to control which workloads
        get scheduled on which nodes, this enables control over how your workload
        interacts with these node taints. More information can be found here:
        https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/
    """

    node_selector: Dict[str, str] = field(default_factory=dict)
    requests: Dict[str, str] = field(default_factory=dict)
    secret_mounts: KubernetesSecretMount = field(default_factory=KubernetesSecretMount)
    tolerations: List[KubernetesToleration] = field(default_factory=list)


@dataclass
class ResourceRequirements:
    kubernetes: KubernetesResourceRequirements = field(
        default_factory=KubernetesResourceRequirements
    )
