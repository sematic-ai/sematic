# Standard Library
from typing import Any, List, Optional, Tuple, Type

# Third-party
from transformers import TrainingArguments

# Sematic
from sematic.types.registry import (
    register_safe_cast,
    register_to_json_encodable,
    register_to_json_encodable_summary,
)
from sematic.types.types.dataclass import (
    safe_cast_dataclass,
    dataclass_to_json_encodable,
    dataclass_to_json_encodable_summary,
)


@register_safe_cast(TrainingArguments)
def _safe_cast_training_arguments(
    value: TrainingArguments, type_: Type[TrainingArguments]
) -> Tuple[Optional[TrainingArguments], Optional[str]]:
    type_ = _fix_training_arguments(type_)
    return safe_cast_dataclass(value, type_)


@register_to_json_encodable(TrainingArguments)
def _training_arguments_to_json_encodable(
    value: TrainingArguments, type_: Type[TrainingArguments]
) -> Any:
    type_ = _fix_training_arguments(type_)
    return dataclass_to_json_encodable(value, type_)


@register_to_json_encodable_summary(TrainingArguments)
def _training_arguments_to_json_encodable_summary(
    value: TrainingArguments, type_: Type[TrainingArguments]
) -> Any:
    type_ = _fix_training_arguments(type_)
    return dataclass_to_json_encodable_summary(value, type_)


def _fix_training_arguments(type_: Type[TrainingArguments]) -> Type[TrainingArguments]:
    """
    HuggingFace's TrainingArguments mutates fields to different types after
    initialization.

    So we need to set the correct types of these fields.
    """
    fields_to_fix = {
        "log_level": int,
        "log_level_replica": int,
        "debug": List[str],
        "sharded_ddp": List[str],
        "fsdp": List[str],
    }

    for name, field_type in fields_to_fix.items():
        field = type_.__dataclass_fields__[name]
        field.type = field_type

    return type_
