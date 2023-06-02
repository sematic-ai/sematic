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


def main():
    resolver = LocalResolver()
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q", "v"],
        lora_dropout=0.05,
        bias="none",
        task_type="SEQ_2_SEQ_LM",
        base_model_name_or_path="",
    )
    training_args = TrainingArguments(
        "temp",
        evaluation_strategy="epoch",
        learning_rate=1e-3,
        gradient_accumulation_steps=1,
        auto_find_batch_size=True,
        num_train_epochs=1,
        save_steps=100,
        save_total_limit=8,
    )
    training_config = TrainingConfig(
        model_size=ModelSize.small,
        lora_config=lora_config,
        training_arguments=training_args,
    )
    dataset_config = DatasetConfig(
        test_fraction=0.1,
    )
    future = pipeline(training_config, dataset_config)
    resolver.resolve(future)


if __name__ == "__main__":
    main()
