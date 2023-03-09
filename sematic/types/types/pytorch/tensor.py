# Standard Library
from typing import Any

# Third-party
import torch

# Sematic
from sematic.types.registry import SummaryOutput, register_to_json_encodable_summary


@register_to_json_encodable_summary(torch.Tensor)
def _torch_tensor_to_json_encodable_summary(
    value: torch.Tensor, type_: Any
) -> SummaryOutput:
    unique_values = value.unique()
    if len(unique_values) < 300:
        unique_values = [i.item() for i in unique_values]
    else:
        unique_values = None

    return {
        "dtype": str(value.dtype),
        "shape": list(value.shape),
        "is_cuda": value.is_cuda,
        "element_size": value.element_size(),
        "is_inference": value.is_inference(),
        "value_range": {"min": value.min().item(), "max": value.max().item()},
        "unique_values": unique_values,
        "has_nan": True in value.isnan(),
        "has_inf": True in value.isinf(),
    }, {}
