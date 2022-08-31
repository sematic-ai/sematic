# Standard Library
from dataclasses import dataclass, field
from typing import Dict


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
    """

    node_selector: Dict[str, str] = field(default_factory=dict)
    requests: Dict[str, str] = field(default_factory=dict)


@dataclass
class ResourceRequirements:
    kubernetes: KubernetesResourceRequirements = field(
        default_factory=KubernetesResourceRequirements
    )
