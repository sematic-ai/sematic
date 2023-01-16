Hello World is fun, but not so useful. Here we show you how to write a real case
training pipeline for the "Hello World" of computer vision, the beloved MNIST.

We will be implementing the model as it is in the [official Pytorch
repository](https://github.com/pytorch/examples/blob/main/mnist/main.py).

You can find the entire code for this example at
[sematic/examples/mnist/pytorch](https://github.com/sematic-ai/sematic/tree/main/sematic/examples/mnist/pytorch).

## Let's create a new project

```shell
$ pip install sematic
$ sematic start
$ sematic new my_mnist_example
```

Or if you want to cheat and get all the code at once, do

```shell
$ sematic new my_mnist_example --from examples/mnist/pytorch
```

## Loading the dataset

Pytorch comes with the baseline MNIST dataset so we'll just use that:

```python
# my_mnist_example/pipeline.py

from torchvision.datasets import MNIST
from torchvision.transforms import Compose, ToTensor, Normalize

@sematic.func
def load_mnist_dataset(train: bool, path: str = "/tmp/pytorch-mnist") -> MNIST:
    """
    Load the MNIST dataset
    """
    transform = Compose([ToTensor(), Normalize((0.1307,), (0.3081,))])
    return MNIST(root=path, train=train, download=True, transform=transform)
```

We will be using the same function to load the train and test dataset by simply
flipping the `train` boolean.

## Getting a dataloader

Now we need to generate a PyTorch dataloader to feed this data into the model
for training and testing.

```python
# my_mnist_example/pipeline.py

from torch.utils.data.dataset import Dataset
from torch.utils.data import DataLoader

@dataclass
class DataLoaderConfig:
    batch_size: Optional[int] = 1000

@sematic.func
def get_dataloader(dataset: Dataset, config: DataLoaderConfig) -> DataLoader:
    """
    Make a Pytorch dataloader
    """
    return DataLoader(dataset, batch_size=config.batch_size)
```

It may be a little overkill to user a dataclass for a single config parameter
but it's generally a good practice to group configs in dataclasses.

Note that the `MNIST` type used at output type of `load_mnist_dataset` is a
subclass of the `Dataset` type used for the `dataset` argument of
`get_dataloader`. This ensures that `get_dataloader` is generic enough to be
usable for arbitrary datasets, not just MNIST.

## Training the model

We have our data ready, let's train the model.

```python
# my_mnist_example/pipeline.py

from torch.optim import Adadelta
from torch.optim.lr_scheduler import StepLR
import torch.nn as nn

@dataclass
class TrainConfig:
    learning_rate: float = 1
    epochs: int = 14
    gamma: float = 0.7
    dry_run: bool = False
    log_interval: int = 10

@sematic.func
def train_model(
    config: TrainConfig, train_loader: DataLoader, device: torch.device,
) -> nn.Module:
    """Train the model"""
    model = Net()
    optimizer = Adadelta(model.parameters(), lr=config.learning_rate)
    scheduler = StepLR(optimizer, step_size=1, gamma=config.gamma)
    for epoch in range(1, config.epochs + 1):
        train(
            model, device, train_loader,
            optimizer, epoch,
            config.log_interval, config.dry_run,
        )
        scheduler.step()

    return model

```

Here `train`, and `Net` were defined in another module. See full code at
[sematic/examples/mnist/pytorch](https://github.com/sematic-ai/sematic/blob/main/sematic/examples/mnist/pytorch/train_eval.py).

## Evaluate the model

Now that the model is trained we want to evaluate its performance on our test dataset.

```python
# my_mnist_example/pipeline.py

import plotly

@dataclass
class EvaluationResults:
    test_set_size: int
    average_loss: float
    accuracy: float
    pr_curve: plotly.graph_objs.Figure
    confusion_matrix: plotly.graph_objs.Figure


@sematic.func
def evaluate_model(
    model: nn.Module, test_loader: DataLoader, device: torch.device
) -> EvaluationResults:
    """
    Evaluate the model.
    """
    results = test(model, device, test_loader)
    return EvaluationResults(
        test_set_size=len(test_loader.dataset),
        average_loss=results["average_loss"],
        accuracy=results["accuracy"],
        pr_curve=results["pr_curve"],
        confusion_matrix=results["confusion_matrix"],
    )
```

## The end-to-end pipeline

Now we can put it all together into an end-to-end pipeline:

```python
# my_mnist_example/pipeline.py

@dataclass
class PipelineConfig:
    dataloader_config: DataLoaderConfig
    train_config: TrainConfig
    use_cuda: bool = False

@sematic.func
def pipeline(config: PipelineConfig) -> EvaluationResults:
    """
    # MNIST example in PyTorch

    As implemented in the
    [PyTorch repository](https://github.com/pytorch/examples/blob/main/mnist/main.py).
    """
    train_dataset = load_mnist_dataset(train=True).set(
        # Setting additional metadata to differentiate the two calls to
        # `load_mnist_dataset` in the UI
        name="Load train dataset", tags=["train"]
    )
    test_dataset = load_mnist_dataset(train=False).set(
        name="Load test dataset", tags=["test"]
    )
    train_dataloader = get_dataloader(
        dataset=train_dataset, config=config.dataloader_config
    )

    test_dataloader = get_dataloader(
        dataset=test_dataset, config=config.dataloader_config
    )

    device = torch.device("cuda" if config.use_cuda else "cpu")

    model = train_model(
        config=config.train_config, train_loader=train_dataloader, device=device
    )

    evaluation_resuts = evaluate_model(
        model=model, test_loader=test_dataloader, device=device
    )

    return evaluation_resuts
```

## The launch script

Now we want to be able to execute this pipeline so we create the launch
script in `my_mnist_example/__main__.py`:

```python
import argparse

from my_mnist_example.pipeline import (
    pipeline,
    PipelineConfig,
    DataLoaderConfig,
    TrainConfig,
)

def main():
    # Parametrize your pipeline as you wish
    parser = argparse.ArgumentParser("My MNIST example")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--version", type=str, default="v0")

    args = parser.parse_args()

    pipeline_config = PipelineConfig(
        dataloader_config=DataLoaderConfig(),
        train_config=TrainConfig(epochs=args.epochs),
    )

    pipeline(pipeline).set(
        name="My MNIST Example", tags=["pytorch", "example", "mnist", args.version]
    ).resolve()


if __name__ == "__main__":
    main()

```

## Let's run!

```shell
$ python3 -m my_mnist_example --epochs 1 --version v1
```

## The execution graph

You should be able to visualize the following execution graph in the UI.

![MNIST graph](./images/GraphPanel.png)

## The evaluation results

And the following evaluation results

![MNIST evaluation](./images/RunPanel.png)