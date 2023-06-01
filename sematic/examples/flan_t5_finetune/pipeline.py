# Standard Library
from dataclasses import dataclass
from typing import Tuple

# Third-party
from datasets import Dataset
from peft import PeftModelForSeq2SeqLM

# Sematic
import sematic
from sematic.examples.flan_t5_finetune.train_eval import (
    DatasetConfig,
    HuggingFaceModelReference,
    ModelSize,
    TrainingConfig,
    prepare_data,
)
from sematic.examples.flan_t5_finetune.train_eval import train as do_train


@dataclass
class ResultSummary:
    source_model: HuggingFaceModelReference
    trained_model: PeftModelForSeq2SeqLM


@sematic.func
def pick_model(model_size: ModelSize) -> HuggingFaceModelReference:
    return HuggingFaceModelReference(owner="google", repo=f"flan-t5-{model_size.value}")


@sematic.func
def train(
    model_reference: HuggingFaceModelReference,
    training_config: TrainingConfig,
    train_data: Dataset,
) -> PeftModelForSeq2SeqLM:
    model = do_train(model_reference.to_string(), training_config, train_data)
    return model


@sematic.func
def prepare_datasets(
    dataset_config: DatasetConfig,
    model_reference: HuggingFaceModelReference,
) -> Tuple[Dataset, Dataset]:
    train_dataset, test_dataset = prepare_data(dataset_config, model_reference)
    return train_dataset, test_dataset


@sematic.func
def summarize(
    source_model: HuggingFaceModelReference, trained_model: PeftModelForSeq2SeqLM
) -> ResultSummary:
    return ResultSummary(
        source_model=source_model,
        trained_model=trained_model,
    )


@sematic.func
def pipeline(
    training_config: TrainingConfig,
    dataset_config: DatasetConfig,
) -> ResultSummary:
    model_ref = pick_model(training_config.model_size)
    train_data, test_data = prepare_datasets(dataset_config, model_ref)
    model = train(model_ref, training_config, train_data)
    return summarize(source_model=model_ref, trained_model=model)
