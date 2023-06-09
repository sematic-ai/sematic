""" Launch script for the FLAN finetuning
isort:skip_file
"""
# Standard Library
import argparse
from dataclasses import replace
from typing import Optional, Tuple

# Third-party
from sematic import torch_patch
from huggingface_hub import login
from peft import LoraConfig, PeftType

# Sematic
from sematic import LocalResolver
from sematic.config.config import switch_env
from sematic.examples.flan_t5_finetune.pipeline import (
    DatasetConfig,
    ModelSize,
    TrainingConfig,
    pipeline,
)
from sematic.examples.flan_t5_finetune.train_eval import (
    HuggingFaceDatasetReference,
    HuggingFaceModelReference,
    TrainingArguments,
)


LORA_CONFIG = LoraConfig(
    r=16,
    lora_alpha=1,
    target_modules=["q", "v"],
    lora_dropout=0.05,
    bias="none",
    peft_type=PeftType.LORA,
    task_type="SEQ_2_SEQ_LM",
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
)

TRAINING_CONFIG = TrainingConfig(
    model_size=ModelSize.base,
    lora_config=LORA_CONFIG,
    training_arguments=TRAINING_ARGS,
    storage_directory="~/tmp/flan-tuned-model",
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
    future = pipeline(training_config, dataset_config, export_reference).set(
        tags=[f"model-size:{training_config.model_size.name}"]
    )
    resolver.resolve(future)


def parse_args() -> Tuple[
    TrainingConfig, DatasetConfig, Optional[HuggingFaceModelReference]
]:
    parser = argparse.ArgumentParser("HuggingFace Flan Example")
    size_options = ", ".join([size.name for size in ModelSize])
    parser.add_argument(
        "--model-size",
        type=lambda size: ModelSize[size],
        default=TRAINING_CONFIG.model_size.name,
        help=(
            f"Select a model size (see https://huggingface.co/google/flan-t5-base)"
            f". Options:  {size_options}."
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
        default=LORA_CONFIG.r,
        help="The number of dimensions for the LoRA matrix.",
    )
    parser.add_argument(
        "--lora-alpha",
        type=int,
        default=LORA_CONFIG.lora_alpha,
        help="The scaling factor for the LoRA trained weights.",
    )
    parser.add_argument(
        "--lora-dropout",
        type=float,
        default=LORA_CONFIG.lora_dropout,
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

    training_config = replace(
        TRAINING_CONFIG,
        model_size=args.model_size,
        training_arguments=replace(
            TRAINING_ARGS,
            learning_rate=args.learning_rate,
            num_train_epochs=args.epochs,
        ),
        lora_config=replace(
            LORA_CONFIG,
            r=args.lora_r,
            lora_alpha=args.lora_alpha,
            lora_dropout=args.lora_dropout,
        ),
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
