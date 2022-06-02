# Standard library
import logging

# Glow
from glow import OfflineResolver

# MNIST example
from glow.examples.mnist.pytorch.calculators import (
    pipeline,
    PipelineConfig,
    DataLoaderConfig,
    TrainConfig,
)


PIPELINE_CONFIG = PipelineConfig(
    dataloader_config=DataLoaderConfig(),
    train_config=TrainConfig(epochs=1),
)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    pipeline(PIPELINE_CONFIG).set(
        name="PyTorch MNIST Example", tags=["pytorch", "example", "mnist"]
    ).resolve(OfflineResolver())
