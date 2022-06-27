# Third-party
from transformers import TrainingArguments

# Sematic
from sematic.types.casting import safe_cast
from sematic.types.serialization import (
    value_to_json_encodable,
    get_json_encodable_summary,
)


def test_safe_cast():
    cast_value, error = safe_cast(TrainingArguments(output_dir=""), TrainingArguments)
    assert error is None


def test_json_encodable():
    value_to_json_encodable(TrainingArguments(output_dir=""), TrainingArguments)


def test_json_encodable_summary():
    get_json_encodable_summary(TrainingArguments(output_dir=""), TrainingArguments)
