"""
This is an example implementation of the MNIST pipeline in PyTorch on sematic.
"""
# MNIST example
import argparse
from sematic.examples.mnist.pytorch.pipeline import (
    pipeline,
    PipelineConfig,
    DataLoaderConfig,
    TrainConfig,
    scan_learning_rate,
)
from sematic import CloudResolver
import logging

logging.basicConfig(level=logging.INFO)


PIPELINE_CONFIG = PipelineConfig(
    dataloader_config=DataLoaderConfig(),
    train_config=TrainConfig(epochs=1),
)


TRAIN_CONFIGS = [
    TrainConfig(epochs=1, learning_rate=0.2),
    TrainConfig(epochs=1, learning_rate=0.4),
    TrainConfig(epochs=1, learning_rate=0.6),
    TrainConfig(epochs=1, learning_rate=0.8),
]


def main():
    parser = argparse.ArgumentParser("MNIST PyTorch example")
    parser.add_argument("--detach", default=False, action="store_true")

    args = parser.parse_args()

    # pipeline(PIPELINE_CONFIG).set(
    #    name="PyTorch MNIST Example", tags=["pytorch", "example", "mnist"]
    # ).resolve(CloudResolver(detach=False))

    scan_learning_rate(
        dataloader_config=DataLoaderConfig(), train_configs=TRAIN_CONFIGS
    ).set(name="Scan MNIST learning rates").resolve(CloudResolver(detach=args.detach))


if __name__ == "__main__":
    main()
