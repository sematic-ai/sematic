# Standard Library
from typing import Any, Dict, List, Literal, Tuple

# Sematic
from sematic.types.registry import register_to_json_encodable_summary

try:
    # Third-party
    import torch
    from ray.train.torch import TorchCheckpoint  # type: ignore
except Exception:
    # Why "Exception" instead of just "ImportError"? Because
    # torch can raise non-standard errors when it fails to import

    # type is not available, so it just won't be registered.
    # Note that the type is not available in "bare ray", but
    # rather only in ray AIR.
    TorchCheckpoint = None


def summarize_ray_torch_checkpoint(
    value: TorchCheckpoint, _
) -> Tuple[Dict[Literal["repr"], str], Dict[str, Any]]:
    # why the "or" instead of get("model", {})? Because if the dict is
    # {"model": None} we would rather replace the None with {}.
    parameters = list((value.to_dict().get("model") or {}).items())
    parameter_summaries: List[str] = []
    if len(parameters) > 0:
        max_key_length = max(len(k) for k, _ in parameters)
        parameter_summaries = []
        for key, value in parameters:
            prefix = key + " " * (max_key_length - len(key))
            parameter_summaries.append(f"{prefix}: {summarize_value(value)}")

    summary = "\n".join(parameter_summaries)
    return {"repr": f"TorchCheckpoint:\n{summary}"}, {}


def summarize_value(value: Any) -> str:
    if torch.is_tensor(value):
        dtype = str(value.dtype).replace("torch.", "")
        dimensions = "x".join([str(dim) for dim in value.size()])
        return f"tensor<{dtype}>({dimensions})"
    else:
        return type(value).__name__


if TorchCheckpoint is not None:
    summarize_ray_torch_checkpoint = register_to_json_encodable_summary(  # type: ignore
        TorchCheckpoint
    )(summarize_ray_torch_checkpoint)
