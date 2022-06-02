import torch
from torchvision.datasets import MNIST
from torch.utils.data import DataLoader
import plotly

import glow


@dataclass
class DataLoaderConfig:
    batch_size: Optional[int] = 1000


@dataclass
class TrainConfig:
    learning_rate: float = 1
    epochs: int = 14
    gamma: float = 0.7
    dry_run: bool = False
    log_interval: int = 10


@dataclass
class PipelineConfig:
    dataloader_config: DataLoaderConfig
    train_config: TrainConfig
    use_cuda: bool = False


@glow.func
def load_mnist_dataset(train: bool, path: str = "/tmp/pytorch-mnist") -> MNIST:
    transform = Compose([ToTensor(), Normalize((0.1307,), (0.3081,))])
    return MNIST(root=path, train=train, download=True, transform=transform)


@glow.func
def get_dataloader(dataset: Dataset, config: DataLoaderConfig) -> DataLoader:
    return DataLoader(dataset, batch_size=config.batch_size)


@glow.func
def train_model(
    config: TrainConfig,
    train_loader: DataLoader,
    device: torch.device,
) -> nn.Module:
    """Train the model"""
    model = Net()
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


@glow.func
class EvaluationResults:
    test_set_size: int
    average_loss: float
    accuracy: FloatInRange[0, 1]
    pr_curve: plotly.graph_objs.Figure


@glow.func
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
    )


@glow.func
def pipeline(config: PipelineConfig) -> EvaluationResults:
    """
    # MNIST example in PyTorch

    As implemented in the [PyTorch repository](https://github.com/pytorch/examples/blob/main/mnist/main.py).
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

    device = torch.device("cuda" if config.use_cuda else "cpu")

    model = train_model(
        config=config.train_config, train_loader=train_dataloader, device=device
    )

    evaluation_resuts = evaluate_model(
        model=model, test_loader=test_dataloader, device=device
    )

    return evaluation_resuts
