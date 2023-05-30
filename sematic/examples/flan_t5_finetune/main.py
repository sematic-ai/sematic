from sematic import LocalResolver
from sematic.examples.flan_t5_finetune.pipeline import TrainingConfig, ModelSize, pipeline


def main():
    resolver = LocalResolver()
    future = pipeline(TrainingConfig(ModelSize.small))

if __name__ == "__main__":
    main()