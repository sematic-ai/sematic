"""
This is an example implementation of the MNIST pipeline in PyTorch on Glow.
"""
# MNIST example
from glow.examples.mnist.pytorch.calculators import (
    pipeline,
    PipelineConfig,
    DataLoaderConfig,
    TrainConfig,
)

from glow import OfflineResolver


PIPELINE_CONFIG = PipelineConfig(
    dataloader_config=DataLoaderConfig(),
    train_config=TrainConfig(epochs=1),
)


if __name__ == "__main__":
    pipeline(PIPELINE_CONFIG).set(
        name="PyTorch MNIST Example", tags=["pytorch", "example", "mnist"]
    ).resolve(OfflineResolver())
