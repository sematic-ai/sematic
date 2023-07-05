# Standard Library
from dataclasses import dataclass
from typing import List, Optional, Tuple

# Third-party
from datasets import Dataset
from transformers import PreTrainedTokenizerBase

# Sematic
import sematic
from sematic.examples.summarization_finetune.interactive import launch_summary_app
from sematic.examples.summarization_finetune.train_eval import (
    DatasetConfig,
    EvaluationResults,
    HuggingFaceModelReference,
    ModelSelection,
    ModelType,
    TrainingConfig,
    evaluate,
    export_model,
)
from sematic.examples.summarization_finetune.train_eval import (
    load_tokenizer as do_load_tokenizer,
)
from sematic.examples.summarization_finetune.train_eval import prepare_data
from sematic.examples.summarization_finetune.train_eval import train as do_train
from sematic.types import HuggingFaceStoredModel as StoredModel
from sematic.types import Link, PromptResponse


@dataclass(frozen=True)
class ResultSummary:
    source_model: HuggingFaceModelReference
    trained_model: StoredModel
    evaluation_results: EvaluationResults
    pushed_model_reference: Optional[HuggingFaceModelReference]
    interactive_eval_transcript: List[PromptResponse]


@sematic.func
def pick_model(model: ModelSelection) -> Tuple[HuggingFaceModelReference, ModelType]:
    if model.value.startswith("flan"):
        size = model.value.replace("flan_", "")
        return (
            HuggingFaceModelReference(owner="google", repo=f"flan-t5-{size}"),
            ModelType.seq_to_seq,
        )
    else:
        name = model.value.replace("_", "-")
        return (
            HuggingFaceModelReference(owner="EleutherAI", repo=name),
            ModelType.causal,
        )


@sematic.func(cache=True)
def load_tokenizer(
    model_reference: HuggingFaceModelReference,
) -> PreTrainedTokenizerBase:
    return do_load_tokenizer(model_reference.to_string())


@sematic.func(cache=True)
def train(
    model_reference: HuggingFaceModelReference,
    training_config: TrainingConfig,
    train_data: Dataset,
    eval_data: Dataset,
    tokenizer: PreTrainedTokenizerBase,
) -> StoredModel:
    model = do_train(
        model_reference.to_string(),
        training_config,
        train_data,
        eval_data,
        tokenizer,
    )
    stored_model = StoredModel.store(
        model, training_config.storage_directory, base_model_reference=model_reference
    )
    return stored_model


@sematic.func
def eval(
    model: StoredModel,
    eval_data: Dataset,
    tokenizer: PreTrainedTokenizerBase,
    model_type: ModelType,
    dataset_config: DatasetConfig,
) -> EvaluationResults:
    return evaluate(
        model.load(device_map="auto", offload_folder="temp/offload"),
        eval_data,
        tokenizer,
        model_type,
        dataset_config,
    )


@sematic.func(cache=True)
def prepare_datasets(
    dataset_config: DatasetConfig,
    tokenizer: PreTrainedTokenizerBase,
    model_type: ModelType,
) -> Tuple[Dataset, Dataset]:
    train_dataset, test_dataset = prepare_data(dataset_config, tokenizer, model_type)
    return train_dataset, test_dataset


@sematic.func
def export(
    model: StoredModel,
    push_model_ref: HuggingFaceModelReference,
) -> HuggingFaceModelReference:
    return export_model(model.load(), push_model_ref)


@sematic.func
def launch_interactively(
    app_url: Link,  # ignored, but makes the link show in the UI
    model: StoredModel,
    tokenizer: PreTrainedTokenizerBase,
    model_type: ModelType,
    max_input_tokens: int,
    max_new_tokens: int,
) -> List[PromptResponse]:
    return launch_summary_app(
        model=model.load(),
        tokenizer=tokenizer,
        model_type=model_type,
        max_input_tokens=max_input_tokens,
        max_new_tokens=max_new_tokens,
    )


@sematic.func(cache=True)
def summarize(
    source_model: HuggingFaceModelReference,
    trained_model: StoredModel,
    evaluation_results: EvaluationResults,
    pushed_model_reference: Optional[HuggingFaceModelReference],
    interactive_eval_transcript: List[PromptResponse],
) -> ResultSummary:
    return ResultSummary(
        source_model=source_model,
        trained_model=trained_model,
        evaluation_results=evaluation_results,
        pushed_model_reference=pushed_model_reference,
        interactive_eval_transcript=interactive_eval_transcript,
    )


@sematic.func
def pipeline(
    training_config: TrainingConfig,
    dataset_config: DatasetConfig,
    export_reference: Optional[HuggingFaceModelReference],
    launch_interactive: bool,
) -> ResultSummary:
    model_ref, model_type = pick_model(training_config.model_selection)
    tokenizer = load_tokenizer(model_ref)
    train_data, test_data = prepare_datasets(dataset_config, tokenizer, model_type)
    model = train(model_ref, training_config, train_data, test_data, tokenizer)
    if launch_interactive:
        transcript = launch_interactively(
            app_url=Link(
                label="Interactive Evaluation App",
                url="http://localhost:7861",
            ),
            model=model,
            tokenizer=tokenizer,
            model_type=model_type,
            max_input_tokens=dataset_config.max_input_length,
            max_new_tokens=dataset_config.max_output_length,
        )
    else:
        transcript = []
    eval_results = eval(model, test_data, tokenizer, model_type, dataset_config)

    exported_model_reference = None
    if export_reference is not None:
        exported_model_reference = export(model, export_reference)

    return summarize(
        source_model=model_ref,
        trained_model=model,
        evaluation_results=eval_results,
        pushed_model_reference=exported_model_reference,
        interactive_eval_transcript=transcript,
    )
