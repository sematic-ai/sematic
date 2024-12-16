# Standard Library
import re
from dataclasses import dataclass, field, replace
from enum import Enum, unique
from typing import Dict, List, Optional, Union
from uuid import uuid4


KUBERNETES_SECRET_NAME = "sematic-func-secrets"


@dataclass(frozen=True)
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
    environment_secrets: Dict[str, str]
        A dict whose keys are the same as the subset of keys from the
        "sematic-func-secret" that you want mounted for the func, and whose values are
        the name of the environment variable where it should be exposed
    file_secrets: Dict[str, str]
        A dict whose keys are the same as the subset of keys from the
        "sematic-func-secret" that you want mounted for the func, and whose values are
        the path to the file within the container where the secret should be exposed.
        These file paths should be RELATIVE paths, they will be taken as relative to
        file_secret_root_path.
    file_secret_root_path: str
        File secrets must all be stored in the same directory. This gives the directory
        where they will be stored. The directory must be a new directory, or the contents
        of the existing directory will be overwritten.
    """

    environment_secrets: Dict[str, str] = field(default_factory=dict)
    file_secrets: Dict[str, str] = field(default_factory=dict)
    file_secret_root_path: str = "/secrets"


@unique
class KubernetesTolerationOperator(Enum):
    """The way that a toleration should be checked to see if it applies.

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
    """The effect that the toleration is meant to tolerate.

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


@dataclass(frozen=True)
class KubernetesToleration:
    """Toleration for a node taint, enabling the pod for the function to run on the node.

    See Kubernetes documentation for more:
    https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/

    Attributes
    ----------
    key: Optional[str]
        The key for the node taint intended to be tolerated. If empty, means
        to match all keys AND all values
    operator: KubernetesTolerationOperator
        The way to compare the key/value pair to the node taint's key/value pair
        to see if the toleration applies
    effect: KubernetesTolerationEffect
        The effect of the node taint the toleration is intended to tolerate.
        Leaving it empty means to tolerate all effects.
    value: Optional[str]
        If the operator is Equals, this value will be compared to the value
        on the node taint to see if this toleration applies.
    toleration_seconds: Optional[int]
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
        """Convert to the format for kwargs the API python client API for tolerations."""
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
        """Ensure that the values in the toleration are valid; raise otherwise.

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


@dataclass(frozen=True)
class KubernetesCapabilities:
    """Capabilities associated with a Kubernetes Security Context.

    For more docs, see:
    https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.27/#capabilities-v1-core

    Attributes
    ----------
    add: List[str]
        Added capabilities
    drop: List[str]
        Dropped capabilities
    """

    add: List[str] = field(default_factory=list)
    drop: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class KubernetesSecurityContext:
    """A security context the Sematic job should run with.

    Docs sourced from:
    https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.27/#securitycontext-v1-core

    Attributes
    ----------
    allow_privilege_escalation: bool
        AllowPrivilegeEscalation controls whether a process can gain more privileges
        than its parent process. This bool directly controls if the no_new_privs
        flag will be set on the container process. AllowPrivilegeEscalation is true
        always when the container is: 1) run as Privileged 2) has CAP_SYS_ADMIN Note
        that this field cannot be set when spec.os.name is windows.
    privileged: bool
        Run container in privileged mode. Processes in privileged containers are
        essentially equivalent to root on the host. Defaults to false. Note that
        this field cannot be set when spec.os.name is windows.
    capabilities: KubernetesCapabilities
        The capabilities to add/drop when running containers. Defaults to the default
        set of capabilities granted by the container runtime. Note that this field
        cannot be set when spec.os.name is windows.
    """

    allow_privilege_escalation: bool
    privileged: bool
    capabilities: KubernetesCapabilities


@dataclass(frozen=True)
class KubernetesHostPathMount:
    """A "hostPath"-type configuration for a volume to mount on the pod to allow access to
    the underlying node's file system.

    More details can be found here:
    https://kubernetes.io/docs/concepts/storage/volumes/#hostpath

    Attributes
    ----------
    node_path: str
        The path on the underlying node to mount into the pod. Corresponds to the "path"
        configuration.
    pod_mount_path: str
        The path where to mount the volume in the pod. Corresponds to the "mountPath"
        configuration.
    name: str
        The name of the volume. Must be an RFC 1123-compliant max 64-character label.
        Corresponds to the "name" configuration. If unspecified, or set as None or empty,
        will default to a label that is auto-generated based on the `pod_mount_path`.
    type: str
        The type of the volume mount. Corresponds to the "type" configuration. Defaults to
        the empty string.
    """

    node_path: str
    pod_mount_path: str
    name: str = field(default="")
    type: str = field(default="")

    def __post_init__(self):
        if not self.name:
            # from the kubernetes documentation:
            # > a lowercase RFC 1123 label must consist of lower case alphanumeric
            # > characters or '-', and must start and end with an alphanumeric character
            # > (e.g. 'my-name', or '123-abc', regex used for validation is
            # > '[a-z0-9]([-a-z0-9]*[a-z0-9])?')
            sanitized = re.sub("_|/|\\s", "-", self.pod_mount_path)
            # pod_mount_path must be absolute, so we know sanitized starts with a dash
            name = f"volume{sanitized}"
            # must also have at most 64 characters
            if len(name) > 64:
                # randomize the last few characters to avoid artificial collisions caused
                # by the truncation, when the user specifies multiple very long paths with
                # the same root
                name = f"{name[:58]}{uuid4().hex[:6]}"

            object.__setattr__(self, "name", name)


@dataclass(frozen=True)
class KubernetesResourceRequirements:
    """Information on the Kubernetes resources required.

    Attributes
    ----------
    node_selector: Dict[str, str]
        The kind of Kubernetes node that the job must run on. More details can
        be found here:
        https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/
        The value of this field will be used as the nodeSelector described there.
    requests: Dict[str, str]
        Requests for resources on a kubernetes pod. More details can be found
        here:
        https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
        The values used here will apply to both the "requests" and the "limits" of the
        job.
    secret_mounts: KubernetesSecretMount
        Requests to take the contents of Kubernetes secrets and expose them as
        environment variables or files on disk when running in the cloud.
    tolerations: List[KubernetesToleration]
        If your Kubernetes configuration uses node taints to control which workloads
        get scheduled on which nodes, this enables control over how your workload
        interacts with these node taints. More information can be found here:
        https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/
    mount_expanded_shared_memory: bool
        By default, Docker uses a 64MB /dev/shm partition. If this flag is set, a
        memory-backed tmpfs that expands up to half of the available memory file is used
        instead. Defaults to False. If that file is expanded to more than that limit
        (through external action), then the pod will be terminated.
    security_context: Optional[KubernetesSecurityContext]
        The Kubernetes security context the job will run with. Note that this
        field will only be respected if `ALLOW_CUSTOM_SECURITY_CONTEXTS` has been
        enabled by your Sematic cluster administrator. Defaults to None.
    host_path_mounts: List[KubernetesHostPathMount]
        The "hostPath"-type configurations for volumes to mount on the pod to allow access
        to the underlying nodes' file systems. Note that thi can only be used if your
        Sematic cluster administrator has enabled the `ALLOW_HOST_PATH_MOUNTING` Server
        setting. Defaults to an empty list. More details can be found here:
        https://kubernetes.io/docs/concepts/storage/volumes/#hostpath
    annotations: Dict[str, str]
        Kubernetes annotations to apply to the created pod. Only annotation keys
        which have been allowed by your Sematic administrator can be used here.
        Others will be ignored.
    labels: Dict[str, str]
        Kubernetes labels to apply to the created pod. Only label keys
        which have been allowed by your Sematic administrator can be used here.
        Others will be ignored.
    """

    node_selector: Dict[str, str] = field(default_factory=dict)
    requests: Dict[str, str] = field(default_factory=dict)
    secret_mounts: KubernetesSecretMount = field(default_factory=KubernetesSecretMount)
    tolerations: List[KubernetesToleration] = field(default_factory=list)
    mount_expanded_shared_memory: bool = field(default=False)
    security_context: Optional[KubernetesSecurityContext] = field(default=None)
    host_path_mounts: List[KubernetesHostPathMount] = field(default_factory=list)
    annotations: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)

    def clone(self) -> "KubernetesResourceRequirements":
        """Deep copy these requirements."""
        # only need to replace things that are mutable.
        return replace(
            self,
            node_selector=dict(self.node_selector),
            requests=dict(self.requests),
            tolerations=[t for t in self.tolerations],
            host_path_mounts=[m for m in self.host_path_mounts],
            annotations=dict(self.annotations),
            labels=dict(self.labels),
        )


@dataclass
class ResourceRequirements:
    kubernetes: KubernetesResourceRequirements = field(
        default_factory=KubernetesResourceRequirements
    )

    def clone(self) -> "ResourceRequirements":
        """Deep copy these resource requirements."""
        return replace(
            self,
            kubernetes=self.kubernetes.clone(),
        )


DEFAULT_RUNNER_RESOURCES = ResourceRequirements(
    kubernetes=KubernetesResourceRequirements(
        requests={"cpu": "500m", "memory": "2Gi"},
    )
)
