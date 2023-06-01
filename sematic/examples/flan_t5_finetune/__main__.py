# Third-party
from peft import LoraConfig

# Sematic
from sematic import LocalResolver
from sematic.examples.flan_t5_finetune.pipeline import (
    DatasetConfig,
    ModelSize,
    TrainingConfig,
    pipeline,
)
from sematic.types.types.aws import S3Location


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
    training_config = TrainingConfig(
        model_size=ModelSize.base,
        lora_config=lora_config,
        checkpoint_location=S3Location.from_uri(
            "s3://sematic-examples/ray-flan-example"
        ),
    )
    dataset_config = DatasetConfig(
        test_fraction=0.1,
    )
    future = pipeline(training_config, dataset_config)
    resolver.resolve(future)


if __name__ == "__main__":
    main()
