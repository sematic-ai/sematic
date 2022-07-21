# Standard library
from typing import List, Optional
from dataclasses import dataclass

# Third-party
import torch
import torch.nn as nn
from torchvision.datasets import MNIST
from torchvision.transforms import Compose, ToTensor, Normalize
from torch.optim import Adadelta
from torch.optim.lr_scheduler import StepLR
from torch.utils.data.dataset import Dataset
from torch.utils.data import DataLoader
import plotly


from sematic.examples.mnist.pytorch.train_eval import train, test, Net

# Sematic
import sematic
from sematic import ResourceRequirements, KubernetesResourceRequirements


@sematic.func(inline=False)
def load_mnist_dataset(train: bool, path: str = "/tmp/pytorch-mnist") -> MNIST:
    transform = Compose([ToTensor(), Normalize((0.1307,), (0.3081,))])
    return MNIST(root=path, train=train, download=True, transform=transform)


@dataclass
class DataLoaderConfig:
    batch_size: Optional[int] = 1000


@sematic.func(inline=False)
def get_dataloader(dataset: Dataset, config: DataLoaderConfig) -> DataLoader:
    return DataLoader(dataset, batch_size=config.batch_size)


@dataclass
class TrainConfig:
    learning_rate: float = 1
    epochs: int = 14
    gamma: float = 0.7
    dry_run: bool = False
    log_interval: int = 10
    cuda: bool = False


@dataclass
class PipelineConfig:
    dataloader_config: DataLoaderConfig
    train_config: TrainConfig
    use_cuda: bool = False


GPU_RESOURCE_REQS = ResourceRequirements(
    kubernetes=KubernetesResourceRequirements(
        node_selector={"node.kubernetes.io/instance-type": "g4dn.xlarge"}
    )
)


@sematic.func(inline=False, resource_requirements=GPU_RESOURCE_REQS)
def train_model(
    config: TrainConfig,
    train_loader: DataLoader,
    device: torch.device,
) -> nn.Module:
    """Train the model"""
    model = Net().to(device)
    optimizer = Adadelta(model.parameters(), lr=config.learning_rate)
    scheduler = StepLR(optimizer, step_size=1, gamma=config.gamma)
    for epoch in range(1, config.epochs + 1):
        train(
            model,
            device,
            train_loader,
            optimizer,
            epoch,
            config.log_interval,
            config.dry_run,
        )
        scheduler.step()

    return model


@dataclass
class EvaluationResults:
    test_set_size: int
    average_loss: float
    accuracy: float
    pr_curve: plotly.graph_objs.Figure
    confusion_matrix: plotly.graph_objs.Figure


@sematic.func(inline=False, resource_requirements=GPU_RESOURCE_REQS)
def evaluate_model(
    model: nn.Module, test_loader: DataLoader, device: torch.device
) -> EvaluationResults:
    """
    Evaluate the model.
    """
    model = model.to(device)
    results = test(model, device, test_loader)
    return EvaluationResults(
        test_set_size=len(test_loader.dataset),  # type: ignore
        average_loss=results["average_loss"],
        accuracy=results["accuracy"],
        pr_curve=results["pr_curve"],
        confusion_matrix=results["confusion_matrix"],
    )


@sematic.func(inline=True)
def train_eval(
    train_dataloader: DataLoader, test_dataloader: DataLoader, train_config: TrainConfig
) -> EvaluationResults:
    """
    The train/eval sub-pipeline.
    """
    device = torch.device("cuda" if train_config.cuda else "cpu")

    model = train_model(
        config=train_config, train_loader=train_dataloader, device=device
    )

    evaluation_results = evaluate_model(
        model=model, test_loader=test_dataloader, device=device
    )

    return evaluation_results


@sematic.func(inline=False)
def pipeline(config: PipelineConfig) -> EvaluationResults:
    """
    # MNIST example in PyTorch

    As implemented in the
    [PyTorch repository](https://github.com/pytorch/examples/blob/main/mnist/main.py).
    """
    train_dataset = load_mnist_dataset(train=True).set(
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

    evaluation_resuts = train_eval(
        train_dataloader=train_dataloader,
        test_dataloader=test_dataloader,
        train_config=config.train_config,
    )

    return evaluation_resuts


@sematic.func(inline=True)
def find_best_accuracy_index(evaluation_results: List[EvaluationResults]) -> int:
    """
    Find the best accuracy out of a list of evaluation results.
    """
    best_accuracy = 0
    best_index = None
    for idx, evaluation_result in enumerate(evaluation_results):
        if evaluation_result.accuracy > best_accuracy:
            best_accuracy = evaluation_result.accuracy
            best_index = idx

    return best_index


@sematic.func(inline=True)
def get_best_learning_rate(configs: List[TrainConfig], best_index: int) -> float:
    return configs[best_index].learning_rate


@sematic.func(inline=True)
def scan_learning_rate(
    dataloader_config: DataLoaderConfig, train_configs: List[TrainConfig]
) -> float:
    """
    Train MNIST with a number of training configurations and extract the one with the
    best accuracy.
    """
    train_dataset = load_mnist_dataset(train=True).set(
        name="Load train dataset", tags=["train"]
    )
    test_dataset = load_mnist_dataset(train=False).set(
        name="Load test dataset", tags=["test"]
    )
    train_dataloader = get_dataloader(dataset=train_dataset, config=dataloader_config)

    test_dataloader = get_dataloader(dataset=test_dataset, config=dataloader_config)

    evaluation_results = [
        train_eval(
            train_dataloader=train_dataloader,
            test_dataloader=test_dataloader,
            train_config=config,
        ).set(name="Train/Eval LR={}".format(config.learning_rate))
        for config in train_configs
    ]

    best_accuracy_index = find_best_accuracy_index(evaluation_results)
    return get_best_learning_rate(train_configs, best_accuracy_index)
