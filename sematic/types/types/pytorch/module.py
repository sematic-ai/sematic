# Standard library
from typing import Any

# Third-party
import torch.nn
import cloudpickle

# Sematic
from sematic.types.registry import (
    register_to_json_encodable,
    register_from_json_encodable,
)
from sematic.types.serialization import binary_from_string, binary_to_string


@register_to_json_encodable(torch.nn.Module)
def _nn_module_to_json_encodable(value: torch.nn.Module, _: Any) -> Any:
    value.cpu()
    return binary_to_string(cloudpickle.dumps(value))


@register_from_json_encodable(torch.nn.Module)
def _nn_module_from_json_encodable(value: str, _: Any) -> torch.nn.Module:
    return cloudpickle.loads(binary_from_string(value))
