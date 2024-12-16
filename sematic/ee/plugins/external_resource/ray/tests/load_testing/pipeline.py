"""
Flexible-structure pipeline meant to be used in load testing.
"""

# Standard Library
import logging
import time
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Tuple

# Third-party
import ray  # type: ignore
import torch
from ray.exceptions import GetTimeoutError  # type: ignore
from torch.optim import Adadelta
from torch.optim.lr_scheduler import StepLR
from torch.utils.data import DataLoader
from torchvision.datasets import MNIST
from torchvision.transforms import Compose, Normalize, ToTensor

# Sematic
from sematic.ee.ray import AutoscalerConfig, RayCluster, RayNodeConfig, SimpleRayCluster
from sematic.examples.mnist.pytorch.train_eval import Net, train
from sematic.function import func


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CollatzResults:
    n_ready: int
    n_not_ready: int
    fraction_ready: float
    results: Dict[int, int]


@dataclass(frozen=True)
class MnistResults:
    n_ready: int
    n_not_ready: int
    fraction_ready: float
    learning_rate_to_loss: List[Tuple[float, float]]


@dataclass(frozen=True)
class CollatzConfig:
    n_workers: int
    n_tasks: int
    wait_minutes: int
    memory_growth_factor: float
    max_n_workers: Optional[int] = None


@dataclass(frozen=True)
class MnistConfig:
    n_rates: int
    n_epochs: int
    n_workers: int
    wait_minutes: int
    max_n_workers: Optional[int] = None


@dataclass(frozen=True)
class LoadResults:
    collatz_results: CollatzResults
    mnist_results: MnistResults


@func(standalone=True)
def collatz_with_ray(
    n_workers: int,
    n_tasks: int,
    wait_minutes: int,
    memory_growth_factor: float,
    max_n_workers: Optional[int] = None,
) -> CollatzResults:
    """
    Specifies the Collatz sequence length for all numbers up to the specified parameter.

    Uses a Ray cluster to accomplish this.
    """
    max_wait_seconds = wait_minutes * 60
    logger.info("Determining max Collatz length for numbers less than %s", n_tasks)
    with RayCluster(
        config=SimpleRayCluster(
            n_nodes=n_workers,
            node_config=RayNodeConfig(cpu=1, memory_gb=2.25),
            max_nodes=max_n_workers,
            autoscaler_config=AutoscalerConfig(
                cpu=0.5,
                memory_gb=1.0,
            ),
        )
    ):
        refs = [
            collatz_ray_task.remote(7, memory_growth_factor) for n in range(0, n_tasks)
        ]
        results = wait_for_results(refs, range(0, n_tasks), max_wait_seconds)
    return CollatzResults(
        n_ready=len(results),
        n_not_ready=len(refs) - len(results),
        fraction_ready=len(results) / len(refs),
        results={k: v for k, v in results},
    )


@ray.remote
def collatz_ray_task(n: int, memory_growth_factor: float):
    # create new logger due to this:
    # https://stackoverflow.com/a/55286452/2540669
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    n_iterations = 0
    intentional_memory_bomb = "x"
    original_n = n
    logger.info("Working on Collatz for %s", original_n)
    while n > 1:
        intentional_memory_bomb = (
            int(memory_growth_factor * len(intentional_memory_bomb)) + 1
        ) * "x"
        n_iterations += 1
        time.sleep(0.01)
        n_mbs = int(len(intentional_memory_bomb) / 2**20)
        if n_mbs > 50:
            logger.info(
                "While working on %s, Bomb size: %s MB",
                original_n,
                n_mbs,
            )
        if n % 2 == 0:
            n = n // 2
        else:
            n = 3 * n + 1
    logger.info("Collatz length of %s: %s", original_n, n_iterations)
    return n_iterations


def wait_for_results(refs, inputs, max_wait_seconds):
    if len(refs) != len(inputs):
        raise ValueError("Object ref count and input count must match")
    start_time = time.time()
    n_ready = 0
    n_total = len(refs)
    n_not_ready = len(refs)
    results_by_ref = {}
    inputs_by_ref = {ref.hex(): input_val for ref, input_val in zip(refs, inputs)}
    remaining_seconds = max_wait_seconds - (time.time() - start_time)
    while n_not_ready != 0 and remaining_seconds > 0:
        for ref in refs:
            if ref.hex() not in results_by_ref:
                try:
                    result = ray.get(ref, timeout=0)
                    results_by_ref[ref.hex()] = result
                except GetTimeoutError:
                    pass  # doesn't matter
                except Exception:
                    logger.exception("Error getting task result")
        time.sleep(10)
        n_ready = len(results_by_ref)
        n_not_ready = n_total - n_ready
        remaining_seconds = max_wait_seconds - (time.time() - start_time)
        logger.info(
            "Progress: %s ready, %s not ready out of %s. %s minutes left",
            n_ready,
            n_not_ready,
            n_total,
            remaining_seconds / 60.0,
        )
    return [
        (inputs_by_ref[ref.hex()], results_by_ref[ref.hex()])
        for ref in refs
        if ref.hex() in results_by_ref
    ]


@func(standalone=True)
def load_test_mnist(
    n_rates: int,
    n_epochs: int,
    n_workers: int,
    wait_minutes: int,
    max_n_workers: Optional[int] = None,
) -> MnistResults:
    learning_rates = [i / (n_rates + 1) for i in range(1, n_rates + 1)]
    max_wait_seconds = wait_minutes * 60
    with RayCluster(
        config=SimpleRayCluster(
            n_nodes=n_workers,
            node_config=RayNodeConfig(cpu=3, memory_gb=12, gpu_count=1),
            max_nodes=max_n_workers,
            autoscaler_config=AutoscalerConfig(
                cpu=0.5,
                memory_gb=1.0,
            ),
        ),
    ):
        refs = [train_model.remote(rate, n_epochs) for rate in learning_rates]
        results = wait_for_results(refs, learning_rates, max_wait_seconds)
    return MnistResults(
        n_ready=len(results),
        n_not_ready=n_rates - len(results),
        fraction_ready=len(results) / n_rates,
        learning_rate_to_loss=results,
    )


@ray.remote(num_cpus=2, num_gpus=1, memory=int(8 * 2**30))
def train_model(
    learning_rate: float,
    n_epochs: int,
) -> Optional[float]:
    """Train the model"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Working on Mnist for %s", learning_rate)
    device = torch.device("cuda")
    path = "/tmp/pytorch-mnist"
    model = Net().to(device)
    optimizer = Adadelta(model.parameters(), lr=learning_rate)
    scheduler = StepLR(optimizer, step_size=1, gamma=0.7)
    log_interval = 10
    batch_size = 1000

    transform = Compose([ToTensor(), Normalize((0.1307,), (0.3081,))])
    mnist_dataset = MNIST(root=path, train=True, download=True, transform=transform)
    train_loader = DataLoader(mnist_dataset, batch_size=batch_size)

    loss = None
    for epoch in range(1, n_epochs + 1):
        loss = train(
            model, device, train_loader, optimizer, epoch, log_interval, dry_run=False
        )
        scheduler.step()

    logger.info(
        "Done with MNIST for learning rate: %s. Final loss: %s",
        learning_rate,
        loss,
    )
    return loss


@func(standalone=False)
def make_results(
    collatz_results: CollatzResults, mnist_results: MnistResults
) -> LoadResults:
    return LoadResults(
        collatz_results=collatz_results,
        mnist_results=mnist_results,
    )


@func(standalone=False)
def load_test_ray(
    collatz_config: Optional[CollatzConfig] = None,
    mnist_config: Optional[MnistConfig] = None,
) -> LoadResults:
    """
    The root function of the testing pipeline.

    Its parameters control the actual shape of the pipeline, according to testing needs.

    Parameters
    ----------
    collatz_config:
        How to perform Collatz load testing (a variety of fairly fast tasks
        with a broad range of lengths and memory requirements).
    mnist_config:
        How to perform MNIST load testing (repeated parallel GPU training
        of MNIST model using different learning rates).
    """
    collatz_results = CollatzResults(
        n_ready=0,
        n_not_ready=0,
        fraction_ready=0,
        results={},
    )

    if collatz_config is not None:
        collatz_results = collatz_with_ray(**asdict(collatz_config))

    mnist_results = MnistResults(
        n_ready=0,
        n_not_ready=0,
        fraction_ready=0.0,
        learning_rate_to_loss=[],
    )
    if mnist_config is not None:
        mnist_results = load_test_mnist(**asdict(mnist_config))

    return make_results(collatz_results, mnist_results)
