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
    FLAN_PROPS,
    GPTJ_PROPS,
    LLAMA_PROPS,
    DatasetConfig,
    EvaluationResults,
    HuggingFaceModelReference,
    ModelSelection,
    ModelType,
    PromptFormat,
    TrainingConfig,
    evaluate,
    export_model,
    prepare_data,
)
from sematic.examples.summarization_finetune.train_eval import (
    load_tokenizer as do_load_tokenizer,
)
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
def pick_model(
    model: ModelSelection, storage_directory: str
) -> Tuple[HuggingFaceModelReference, ModelType, PromptFormat]:
    if model.value.startswith("flan"):
        size = model.value.replace("flan_", "")
        return (
            HuggingFaceModelReference(owner="google", repo=f"flan-t5-{size}"),
            ModelType.seq_to_seq,
            FLAN_PROPS.prompt_format,
        )
    elif "gpt" in model.value:
        name = model.value.replace("_", "-")
        return (
            HuggingFaceModelReference(owner="EleutherAI", repo=name),
            ModelType.causal,
            GPTJ_PROPS.prompt_format,
        )
    else:
        name = model.value.replace("_", "-")
        name = f"L{name[1:]}"  # captialize starting L
        return (
            HuggingFaceModelReference(
                owner="meta-llama",
                repo=f"{name}-hf",
            ),
            ModelType.causal,
            LLAMA_PROPS.prompt_format,
        )


@sematic.func(cache=True)
def load_tokenizer(
    model_reference: HuggingFaceModelReference,
) -> PreTrainedTokenizerBase:
    return do_load_tokenizer(model_reference)


@sematic.func(cache=True)
def train(
    model_reference: HuggingFaceModelReference,
    training_config: TrainingConfig,
    train_data: Dataset,
    eval_data: Dataset,
    tokenizer: PreTrainedTokenizerBase,
) -> StoredModel:
    model = do_train(
        model_reference,
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
    prompt_format: PromptFormat,
) -> EvaluationResults:
    return evaluate(
        model.load(device_map="auto", offload_folder="temp/offload"),
        eval_data,
        tokenizer,
        model_type,
        dataset_config,
        prompt_format,
    )


@sematic.func(cache=True)
def prepare_datasets(
    dataset_config: DatasetConfig,
    tokenizer: PreTrainedTokenizerBase,
    model_type: ModelType,
    prompt_format: PromptFormat,
) -> Tuple[Dataset, Dataset]:
    train_dataset, test_dataset = prepare_data(
        dataset_config, tokenizer, model_type, prompt_format
    )
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
    prompt_format: PromptFormat,
) -> List[PromptResponse]:
    return launch_summary_app(
        model=model.load(),
        tokenizer=tokenizer,
        model_type=model_type,
        max_input_tokens=max_input_tokens,
        max_new_tokens=max_new_tokens,
        prompt_format=prompt_format,
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
    model_ref, model_type, prompt_format = pick_model(
        training_config.model_selection, training_config.storage_directory
    )
    tokenizer = load_tokenizer(model_ref)
    train_data, test_data = prepare_datasets(
        dataset_config, tokenizer, model_type, prompt_format
    )
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
            prompt_format=prompt_format,
        )
    else:
        transcript = []
    eval_results = eval(
        model, test_data, tokenizer, model_type, dataset_config, prompt_format
    )

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
