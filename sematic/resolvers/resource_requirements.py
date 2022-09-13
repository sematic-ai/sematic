# Standard Library
from dataclasses import dataclass, field
from typing import Dict

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
    """

    node_selector: Dict[str, str] = field(default_factory=dict)
    requests: Dict[str, str] = field(default_factory=dict)
    secret_mounts: KubernetesSecretMount = field(default_factory=KubernetesSecretMount)


@dataclass
class ResourceRequirements:
    kubernetes: KubernetesResourceRequirements = field(
        default_factory=KubernetesResourceRequirements
    )
