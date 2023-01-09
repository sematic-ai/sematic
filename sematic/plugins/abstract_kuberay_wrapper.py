# Standard Library
from dataclasses import dataclass, field
from typing import Dict, Optional, Union


@dataclass(frozen=True)
class RayNode:
    cpu: float
    memory_gb: float
    gpu_count: int
    gpu_kind: Optional[str] = None
    additional_configuration: Dict[str, Union[str, float, int, bool]] = field(
        default_factory=dict
    )
