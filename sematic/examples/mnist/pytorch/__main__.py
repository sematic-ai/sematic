"""
This is an example implementation of the MNIST pipeline in PyTorch on sematic.
"""
# MNIST example
from sematic.examples.mnist.pytorch.pipeline import (
    pipeline,
    PipelineConfig,
    DataLoaderConfig,
    TrainConfig,
)
from sematic import CloudResolver


PIPELINE_CONFIG = PipelineConfig(
    dataloader_config=DataLoaderConfig(),
    train_config=TrainConfig(epochs=1),
)


def main():
    """
    Entry point for examples/mnist/pytorch

    Run with

    ```shell
    $ sematic run examples/mnist/pytorch
    ```
    """
    pipeline(PIPELINE_CONFIG).set(
        name="PyTorch MNIST Example", tags=["pytorch", "example", "mnist"]
    ).resolve(CloudResolver())


if __name__ == "__main__":
    main()
