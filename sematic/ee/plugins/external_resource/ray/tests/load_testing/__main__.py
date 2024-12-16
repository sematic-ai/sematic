"""
Entry point for the testing pipeline.
"""

# Standard Library
import argparse
import logging
import os
from typing import Optional, Tuple

# Third-party
import debugpy  # type: ignore

# Sematic
from sematic import CloudRunner, LocalRunner, Runner, SilentRunner
from sematic.ee.plugins.external_resource.ray.tests.load_testing.pipeline import (
    CollatzConfig,
    MnistConfig,
    load_test_ray,
)


logger = logging.getLogger(__name__)

BAZEL_COMMAND = (
    "bazel run "
    "//sematic/ee/plugins/external_resource/ray/tests/load_testing:__main__ "
    "--"
)
DESCRIPTION = (
    "This pipeline is used to perform load testing on the Ray integration. "
    "There are two kinds of load test: Collatz and MNIST. Collatz load testing "
    "uses a large number of independent tasks with varying (but small) compute "
    "and memory usage needs. It can be configured to begin OOM'ing tasks for "
    "some workloads. MNIST load testing performs GPU training of an MNIST model "
    "with a variety of learning rates."
)
CLOUD_HELP = (
    "Whether to run the pipeline in the cloud, or locally. Defaults to False. "
    "Only one of --silent or --cloud are allowed."
)
SILENT_HELP = (
    "Whether to run the pipeline using the SilentRunner. Defaults to False. "
    "Only one of --silent or --cloud are allowed."
)
COLLATZ_N_WORKERS_HELP = "Number of workers when doing the Collatz load test"
COLLATZ_MAX_N_WORKERS_HELP = "Maximum number of workers when doing the Collatz load test"
COLLATZ_N_TASKS_HELP = "Number of tasks to perform operations on for Collatz load test"
COLLATZ_WAIT_MINUTES_HELP = (
    "Number of minutes to wait before stopping the Collatz load test"
)
COLLATZ_MEMORY_GROWTH_FACTOR_HELP = (
    "For each Collatz task, how rapidly should memory usage grow per iteration in the "
    "task? A factor of 1.25 grows at about a rate of an extra 25 percent per iteration, "
    "and is enough to OOM for tasks around 100. 1.0 should be safe to not OOM."
)
MNIST_N_RATES_HELP = (
    "Number of different learning rates (independent training jobs) to try."
)
MNIST_N_EPOCHS_HELP = "Number of training epochs for each training job to try."
MNIST_N_WORKERS_HELP = (
    "Number of Ray workers (including head) to use in the cluster. Set to 0 "
    "(default) to disable MNIST load testing."
)
MNIST_MAX_N_WORKERS_HELP = (
    "Max number of Ray workers (including head) to use in the cluster. Set to 0 "
    "(default) to disable MNIST load testing."
)
MNIST_WAIT_MINUTES_HELP = "Number of minutes to wait before stopping the Mnist load test."


def _parse_args() -> (
    Tuple[argparse.Namespace, Optional[CollatzConfig], Optional[MnistConfig]]
):
    """Parses the command line arguments."""
    parser = argparse.ArgumentParser(prog=BAZEL_COMMAND, description=DESCRIPTION)

    # Runner args:
    parser.add_argument(
        "--cloud",
        action="store_true",
        default=False,
        help=CLOUD_HELP,
    )
    parser.add_argument(
        "--silent",
        action="store_true",
        default=False,
        help=SILENT_HELP,
    )
    parser.add_argument(
        "--collatz.n_workers",
        type=int,
        default=0,
        dest="collatz_n_workers",
        help=COLLATZ_N_WORKERS_HELP,
    )
    parser.add_argument(
        "--collatz.max_n_workers",
        type=int,
        default=0,
        dest="collatz_max_n_workers",
        help=COLLATZ_MAX_N_WORKERS_HELP,
    )
    parser.add_argument(
        "--collatz.n_tasks",
        type=int,
        default=10,
        dest="collatz_n_tasks",
        help=COLLATZ_N_TASKS_HELP,
    )
    parser.add_argument(
        "--collatz.wait_minutes",
        type=int,
        default=1,
        dest="collatz_wait_minutes",
        help=COLLATZ_WAIT_MINUTES_HELP,
    )
    parser.add_argument(
        "--collatz.memory_growth_factor",
        type=float,
        default=1.10,
        dest="collatz_memory_growth_factor",
        help=COLLATZ_MEMORY_GROWTH_FACTOR_HELP,
    )

    parser.add_argument(
        "--mnist.n_rates",
        type=int,
        default=10,
        dest="mnist_n_rates",
        help=MNIST_N_RATES_HELP,
    )
    parser.add_argument(
        "--mnist.n_epochs",
        type=int,
        default=10,
        dest="mnist_n_epochs",
        help=MNIST_N_EPOCHS_HELP,
    )
    parser.add_argument(
        "--mnist.n_workers",
        type=int,
        default=0,
        dest="mnist_n_workers",
        help=MNIST_N_WORKERS_HELP,
    )
    parser.add_argument(
        "--mnist.max_n_workers",
        type=int,
        default=0,
        dest="mnist_max_n_workers",
        help=MNIST_MAX_N_WORKERS_HELP,
    )
    parser.add_argument(
        "--mnist.wait_minutes",
        type=int,
        default=10,
        dest="mnist_wait_minutes",
        help=MNIST_WAIT_MINUTES_HELP,
    )

    args = parser.parse_args()

    if args.silent and args.cloud:
        raise ValueError("Cannot pass --silent and --cloud")

    collatz_config_args = {
        arg_key.replace("collatz_", ""): arg_val
        for arg_key, arg_val in vars(args).items()
        if arg_key.startswith("collatz_")
    }
    collatz_config: Optional[CollatzConfig] = CollatzConfig(**collatz_config_args)
    if collatz_config.n_workers == 0:  # type: ignore
        collatz_config = None

    mnist_config_args = {
        arg_key.replace("mnist_", ""): arg_val
        for arg_key, arg_val in vars(args).items()
        if arg_key.startswith("mnist_")
    }
    mnist_config: Optional[MnistConfig] = MnistConfig(**mnist_config_args)
    if mnist_config.n_workers == 0:  # type: ignore
        mnist_config = None

    return args, collatz_config, mnist_config


def _get_runner(args: argparse.Namespace) -> Runner:
    """Instantiates the Runner based on the passed arguments."""
    if args.silent:
        return SilentRunner()
    if not args.cloud:
        return LocalRunner()

    return CloudRunner(
        detach=True,
    )


def _wait_for_debugger():
    debugpy.listen(5724)

    print("Waiting for debugger to attach...")
    debugpy.wait_for_client()
    print("Debugger attached")


def main() -> None:
    if os.environ.get("DEBUGPY", None) is not None:
        _wait_for_debugger()

    args, collatz_config, mnist_config = _parse_args()
    logger.info("Command line arguments: %s", args)
    tags = ["load-testing", "ray"]

    if collatz_config is not None:
        tags.append("collatz-tested")

    if mnist_config is not None:
        tags.append("mnist-tested")

    runner = _get_runner(args)

    future = load_test_ray(collatz_config, mnist_config).set(
        name="Load Test Ray",
        tags=tags,
    )

    logger.info("Invoking the pipeline...")
    result = runner.run(future)
    logger.info("Pipeline result: %s", result)


if __name__ == "__main__":
    main()
