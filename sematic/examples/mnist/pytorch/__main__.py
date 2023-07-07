"""
This is an example implementation of the MNIST pipeline in PyTorch on sematic.
"""
# Sematic
# MNIST example
from sematic import LocalRunner
from sematic.examples.mnist.pytorch.pipeline import (
    DataLoaderConfig,
    PipelineConfig,
    TrainConfig,
    pipeline,
)

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
    LocalRunner().run(
        pipeline(PIPELINE_CONFIG).set(
            name="PyTorch MNIST Example", tags=["pytorch", "example", "mnist"]
        )
    )


if __name__ == "__main__":
    main()
