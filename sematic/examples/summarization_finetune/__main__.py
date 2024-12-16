"""Launch script for the summarization model finetuning
isort:skip_file
"""

# Standard Library
import argparse
import logging
from dataclasses import dataclass, replace
from typing import Optional

from huggingface_hub import login
from peft import LoraConfig, PeftType

# Third-party
# Sematic
from sematic import (
    LocalRunner,
    torch_patch,  # noqa: F401
)
from sematic.examples.summarization_finetune.pipeline import (
    DatasetConfig,
    ModelSelection,
    TrainingConfig,
    pipeline,
)
from sematic.examples.summarization_finetune.train_eval import (
    HuggingFaceDatasetReference,
    HuggingFaceModelReference,
    TrainingArguments,
)


LORA_CONFIG_FLAN = LoraConfig(
    r=16,
    lora_alpha=1,
    target_modules=["q", "v"],
    lora_dropout=0.05,
    bias="none",
    peft_type=PeftType.LORA,
    task_type="SEQ_2_SEQ_LM",
    base_model_name_or_path="",
)

LORA_CONFIG_GPT_J = replace(
    LORA_CONFIG_FLAN,
    target_modules=[
        "q_proj",
        "v_proj",
    ],
    task_type="CAUSAL_LM",
    base_model_name_or_path="",
)

LORA_LLAMA_2 = replace(
    LORA_CONFIG_FLAN,
    target_modules=[
        "q_proj",
        "v_proj",
    ],
    task_type="CAUSAL_LM",
    base_model_name_or_path="",
)

TRAINING_ARGS = TrainingArguments(
    "temp",
    evaluation_strategy="epoch",
    learning_rate=1e-3,
    gradient_accumulation_steps=1,
    auto_find_batch_size=True,
    num_train_epochs=1,
    save_strategy="epoch",
    save_total_limit=8,
    logging_steps=100,
)

TRAINING_CONFIG = TrainingConfig(
    model_selection=ModelSelection.flan_base,
    lora_config=LORA_CONFIG_FLAN,
    training_arguments=TRAINING_ARGS,
    storage_directory="/tmp/summarization-tuned-model",
)

DATASET_CONFIG = DatasetConfig(
    max_input_length=1024,
    max_output_length=256,
    max_train_samples=None,
    max_test_samples=None,
    dataset_ref=HuggingFaceDatasetReference.from_string("cnn_dailymail:1.0.0"),
    text_column="article",
    summary_column="highlights",
)


def main():
    logging.basicConfig(level=logging.INFO)
    parsed_args = parse_args()
    runner = LocalRunner(cache_namespace=parsed_args.cache_namespace)
    model_tag = parsed_args.training_config.model_selection.name.replace("_", "-")
    future = pipeline(
        training_config=parsed_args.training_config,
        dataset_config=parsed_args.dataset_config,
        export_reference=parsed_args.export_reference,
        launch_interactive=parsed_args.launch_interactive,
    ).set(
        name="Summarization Fine-Tuning",
        tags=[f"model-selection:{model_tag}"],
    )
    runner.run(future)


@dataclass(frozen=True)
class ParsedArgs:
    training_config: TrainingConfig
    dataset_config: DatasetConfig
    export_reference: Optional[HuggingFaceModelReference]
    cache_namespace: Optional[str]
    launch_interactive: bool


def parse_args() -> ParsedArgs:
    parser = argparse.ArgumentParser("Hugging Face Summarization Example")
    selection_options = ", ".join(
        [selection.name.replace("_", "-") for selection in ModelSelection]
    )
    parser.add_argument(
        "--model-selection",
        type=lambda selection: ModelSelection[selection.replace("-", "_")],
        default=TRAINING_CONFIG.model_selection,
        help=(f"Select a model" f". Options:  {selection_options}."),
    )
    (
        parser.add_argument(
            "--epochs",
            type=int,
            default=1,
            help="The number of epochs to train on.",
        ),
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=TRAINING_ARGS.learning_rate,
        help="The learning rate for the training.",
    )
    parser.add_argument(
        "--logging-steps",
        type=int,
        default=TRAINING_ARGS.logging_steps,
        help="Number of steps between logging metrics during training.",
    )
    parser.add_argument(
        "--max-train-samples",
        type=int,
        default=DATASET_CONFIG.max_train_samples,
        help="Maximum number of samples in a single training epoch.",
    )
    parser.add_argument(
        "--max-test-samples",
        type=int,
        default=DATASET_CONFIG.max_test_samples,
        help="Maximum number of samples in testing.",
    )
    parser.add_argument(
        "--max-input-length",
        type=int,
        default=DATASET_CONFIG.max_input_length,
        help="Maximum number of tokens in the input prompt.",
    )
    parser.add_argument(
        "--max-output-length",
        type=int,
        default=DATASET_CONFIG.max_output_length,
        help="Maximum number of output tokens in response to the prompt.",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=DATASET_CONFIG.dataset_ref.to_string(),
        help=(
            "The Hugging Face dataset to use. Should be structured as: "
            "<owner>/<repo>:<subset>. For datasets owned by HuggingFace, omit <owner>/ "
            "Ex: cnn_dailymail:1.0.0 for https://huggingface.co/datasets/cnn_dailymail"
        ),
    )
    parser.add_argument(
        "--text-column",
        type=str,
        default=DATASET_CONFIG.text_column,
        help=(
            "The name of the column in the source dataset holding the text to summarize"
        ),
    )
    parser.add_argument(
        "--summary-column",
        type=str,
        default=DATASET_CONFIG.summary_column,
        help=(
            "The name of the column in the source dataset holding the summary of "
            "the text."
        ),
    )
    parser.add_argument(
        "--model-export-repo",
        type=str,
        default=None,
        help=(
            "A huggingface repo to export the model to. "
            "Should be provided as <repo-owner>/<repo name>."
        ),
    )
    parser.add_argument(
        "--lora-r",
        type=int,
        default=LORA_CONFIG_FLAN.r,
        help="The number of dimensions for the LoRA matrix.",
    )
    parser.add_argument(
        "--lora-alpha",
        type=int,
        default=LORA_CONFIG_FLAN.lora_alpha,
        help="The scaling factor for the LoRA trained weights.",
    )
    parser.add_argument(
        "--lora-dropout",
        type=float,
        default=LORA_CONFIG_FLAN.lora_dropout,
        help="The dropout probability for LoRA layers.",
    )
    parser.add_argument(
        "--login",
        default=False,
        action="store_true",
        help=(
            "Whether or not to prompt for HuggingFace login. "
            "Should be done on first script execution."
        ),
    )
    parser.add_argument(
        "--cache-namespace",
        type=str,
        default=None,
        help="Namespace under which cached values will be stored and retrieved.",
    )
    parser.add_argument(
        "--launch-interactively",
        action="store_true",
        default=False,
        help="Launch an interactive Gradio app to test the model.",
    )
    parser.add_argument(
        "--storage-directory",
        type=str,
        default=TRAINING_CONFIG.storage_directory,
        help=(
            "Directory used to store objects related to pipeline execution. "
            "If you are using Llama 2, this directory must contain a subdirectory "
            "named 'llama' that contains the tokenizer and models downloaded from Meta."
        ),
    )

    args = parser.parse_args()

    lora_config = LORA_CONFIG_GPT_J
    if args.model_selection.is_flan():
        lora_config = LORA_CONFIG_FLAN
    elif args.model_selection.is_llama():
        lora_config = LORA_LLAMA_2

    lora_config = replace(
        lora_config,
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
    )
    training_config = replace(
        TRAINING_CONFIG,
        model_selection=args.model_selection,
        training_arguments=replace(
            TRAINING_ARGS,
            learning_rate=args.learning_rate,
            num_train_epochs=args.epochs,
            logging_steps=args.logging_steps,
        ),
        storage_directory=args.storage_directory,
        lora_config=lora_config,
    )

    dataset_config = replace(
        DATASET_CONFIG,
        max_train_samples=args.max_train_samples,
        max_test_samples=args.max_test_samples,
        max_input_length=args.max_input_length,
        max_output_length=args.max_output_length,
        dataset_ref=HuggingFaceDatasetReference.from_string(args.dataset),
        text_column=args.text_column,
        summary_column=args.summary_column,
    )
    if dataset_config.dataset_ref.commit_sha is not None:
        raise ValueError("Using a specific commit of a dataset is not supported.")

    export_model_reference = None
    if args.model_export_repo is not None:
        export_model_reference = HuggingFaceModelReference.from_string(
            args.model_export_repo
        )

    if args.login:
        login()

    return ParsedArgs(
        training_config,
        dataset_config,
        export_model_reference,
        args.cache_namespace,
        args.launch_interactively,
    )


if __name__ == "__main__":
    main()
