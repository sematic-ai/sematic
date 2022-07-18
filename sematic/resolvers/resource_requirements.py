# Standard library
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class KubernetesResourceRequirements:
    node_selector: Dict[str, str] = field(default_factory=dict)


@dataclass
class ResourceRequirements:
    kubernetes: KubernetesResourceRequirements = field(
        default_factory=KubernetesResourceRequirements
    )
