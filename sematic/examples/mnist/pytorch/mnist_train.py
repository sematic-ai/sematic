"""
This is an example implementation of the MNIST training pipeline in PyTorch on
Sematic, using the CloudResolver.

This is the same pipeline from the local example in __main__.py.
"""
# Standard Library
# MNIST example
import argparse
import logging

# Sematic
from sematic import CloudResolver, LocalResolver
from sematic.examples.mnist.pytorch.pipeline import (
    DataLoaderConfig,
    PipelineConfig,
    TrainConfig,
    pipeline,
)

logging.basicConfig(level=logging.INFO)

TRAIN_CONFIGS = [
    TrainConfig(epochs=1, learning_rate=0.2),
    TrainConfig(epochs=5, learning_rate=0.4),
    TrainConfig(epochs=5, learning_rate=0.6),
    TrainConfig(epochs=5, learning_rate=0.8),
]


def main():
    parser = argparse.ArgumentParser("PyTorch MNIST Example")
    parser.add_argument("--detach", default=False, action="store_true")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--learning-rate", type=float, default="1")
    parser.add_argument("--cuda", default=False, action="store_true")
    parser.add_argument("--rerun-from", type=str, default=None)
    parser.add_argument("--cloud", default=False, action="store_true")

    args = parser.parse_args()

    train_config = TrainConfig(
        epochs=args.epochs, learning_rate=args.learning_rate, cuda=args.cuda
    )

    config = PipelineConfig(
        dataloader_config=DataLoaderConfig(), train_config=train_config
    )

    resolver = (
        CloudResolver(detach=args.detach, rerun_from=args.rerun_from)
        if args.cloud
        else LocalResolver(rerun_from=args.rerun_from)
    )

    pipeline(config=config).set(
        name="PyTorch MNIST Example", tags=["pytorch", "example", "mnist"]
    ).resolve(resolver)


if __name__ == "__main__":
    main()
