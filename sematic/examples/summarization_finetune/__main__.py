""" Launch script for the summarization model finetuning
isort:skip_file
"""
# Standard Library
import argparse
from dataclasses import replace
from typing import Optional, Tuple

# Third-party
from sematic import torch_patch  # noqa: F401
from huggingface_hub import login
from peft import LoraConfig, PeftType

# Sematic
from sematic import LocalResolver
from sematic.config.config import switch_env
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

LORA_CONFIG_FALCON = replace(
    LORA_CONFIG_FLAN,
    target_modules=[
        "query_key_value",
        "dense",
        "dense_h_to_4h",
        "dense_4h_to_h",
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
    save_steps=100,
    save_total_limit=8,
    logging_steps=100,
)

TRAINING_CONFIG = TrainingConfig(
    model_selection=ModelSelection.flan_base,
    lora_config=LORA_CONFIG_FLAN,
    training_arguments=TRAINING_ARGS,
    storage_directory="~/tmp/summarization-tuned-model",
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
    switch_env("user")

    training_config, dataset_config, export_reference = parse_args()
    resolver = LocalResolver()
    model_tag = training_config.model_selection.name.replace("_", "-")
    future = pipeline(training_config, dataset_config, export_reference).set(
        name="Summarization Fine-Tuning",
        tags=[f"model-selection:{model_tag}"],
    )
    resolver.resolve(future)


def parse_args() -> Tuple[
    TrainingConfig, DatasetConfig, Optional[HuggingFaceModelReference]
]:
    parser = argparse.ArgumentParser("Hugging Face Summarization Example")
    selection_options = ", ".join([selection.name.replace("_", "-") for selection in ModelSelection])
    parser.add_argument(
        "--model-selection",
        type=lambda selection: ModelSelection[selection.replace("-", "_")],
        default=TRAINING_CONFIG.model_selection.name,
        help=(
            f"Select a model"
            f". Options:  {selection_options}."
        ),
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=1,
        help="The number of epochs to train on.",
    ),
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
        )
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
    args = parser.parse_args()

    lora_config = replace(
        LORA_CONFIG_FLAN if args.model_selection.is_flan() else LORA_CONFIG_FALCON,
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

    return training_config, dataset_config, export_model_reference


if __name__ == "__main__":
    main()
