# Standard Library
import argparse
from dataclasses import replace

# Third-party
from peft import LoraConfig
from transformers import TrainingArguments

# Sematic
from sematic import LocalResolver
from sematic.examples.flan_t5_finetune.pipeline import (
    DatasetConfig,
    ModelSize,
    TrainingConfig,
    pipeline,
)
from sematic.examples.flan_t5_finetune.train_eval import TrainingArguments

LORA_CONFIG = LoraConfig(
    r=16,
    lora_alpha=1,
    target_modules=["q", "v"],
    lora_dropout=0.05,
    bias="none",
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
)


def main():
    training_config, dataset_config = parse_args()
    resolver = LocalResolver()
    future = pipeline(training_config, dataset_config).set(
        tags=[f"model-size:{training_config.model_size.name}"]
    )
    resolver.resolve(future)


def parse_args():
    parser = argparse.ArgumentParser("HuggingFace Flan Example")
    parser.add_argument(
        "--model-size", type=str, default=TRAINING_CONFIG.model_size.name
    )
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument(
        "--learning-rate", type=float, default=TRAINING_ARGS.learning_rate
    )
    parser.add_argument(
        "--max-train-samples", type=int, default=DATASET_CONFIG.max_train_samples
    )
    parser.add_argument(
        "--max-test-samples", type=int, default=DATASET_CONFIG.max_test_samples
    )
    parser.add_argument(
        "--max-input-length", type=int, default=DATASET_CONFIG.max_input_length
    )
    parser.add_argument(
        "--max-output-length", type=int, default=DATASET_CONFIG.max_output_length
    )
    args = parser.parse_args()

    training_config = replace(
        TRAINING_CONFIG,
        model_size=ModelSize[args.model_size],
        training_arguments=replace(
            TRAINING_ARGS,
            learning_rate=args.learning_rate,
            num_train_epochs=args.epochs,
        ),
    )

    dataset_config = replace(
        DATASET_CONFIG,
        max_train_samples=args.max_train_samples,
        max_test_samples=args.max_test_samples,
        max_input_length=args.max_input_length,
        max_output_length=args.max_output_length,
    )

    return training_config, dataset_config


if __name__ == "__main__":
    main()
