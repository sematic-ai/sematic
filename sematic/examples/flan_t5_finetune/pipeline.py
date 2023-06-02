# Standard Library
from dataclasses import dataclass
from typing import Tuple

# Third-party
from datasets import Dataset
from peft import PeftModelForSeq2SeqLM
from transformers import PreTrainedTokenizerBase

# Sematic
import sematic
from sematic.examples.flan_t5_finetune.train_eval import (
    DatasetConfig,
    EvaluationResults,
    HuggingFaceModelReference,
    ModelSize,
    TrainingConfig,
    evaluate,
)
from sematic.examples.flan_t5_finetune.train_eval import (
    load_tokenizer as do_load_tokenizer,
)
from sematic.examples.flan_t5_finetune.train_eval import prepare_data
from sematic.examples.flan_t5_finetune.train_eval import train as do_train


@dataclass
class ResultSummary:
    source_model: HuggingFaceModelReference
    trained_model: PeftModelForSeq2SeqLM
    evaluation_results: EvaluationResults


@sematic.func
def pick_model(model_size: ModelSize) -> HuggingFaceModelReference:
    return HuggingFaceModelReference(owner="google", repo=f"flan-t5-{model_size.value}")


@sematic.func
def load_tokenizer(
    model_reference: HuggingFaceModelReference,
) -> PreTrainedTokenizerBase:
    return do_load_tokenizer(model_reference.to_string())


@sematic.func
def train(
    model_reference: HuggingFaceModelReference,
    training_config: TrainingConfig,
    train_data: Dataset,
    eval_data: Dataset,
) -> PeftModelForSeq2SeqLM:
    model = do_train(
        model_reference.to_string(),
        training_config,
        train_data,
        eval_data,
    )
    return model


@sematic.func
def eval(
    model: PeftModelForSeq2SeqLM,
    eval_data: Dataset,
    tokenizer: PreTrainedTokenizerBase,
) -> EvaluationResults:
    return evaluate(model, eval_data, tokenizer)


@sematic.func
def prepare_datasets(
    dataset_config: DatasetConfig,
    tokenizer: PreTrainedTokenizerBase,
) -> Tuple[Dataset, Dataset]:
    train_dataset, test_dataset = prepare_data(dataset_config, tokenizer)
    return train_dataset, test_dataset


@sematic.func
def summarize(
    source_model: HuggingFaceModelReference,
    trained_model: PeftModelForSeq2SeqLM,
    evaluation_results: EvaluationResults,
) -> ResultSummary:
    return ResultSummary(
        source_model=source_model,
        trained_model=trained_model,
        evaluation_results=evaluation_results,
    )


@sematic.func
def pipeline(
    training_config: TrainingConfig,
    dataset_config: DatasetConfig,
) -> ResultSummary:
    model_ref = pick_model(training_config.model_size)
    tokenizer = load_tokenizer(model_ref)
    train_data, test_data = prepare_datasets(dataset_config, tokenizer)
    model = train(model_ref, training_config, train_data, test_data)
    eval_results = eval(model, test_data, tokenizer)
    return summarize(
        source_model=model_ref, trained_model=model, evaluation_results=eval_results
    )
