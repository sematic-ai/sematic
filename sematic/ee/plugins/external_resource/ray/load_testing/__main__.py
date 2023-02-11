"""
Entry point for the testing pipeline.
"""
# Standard Library
import argparse
import logging
import os

# Third-party
import debugpy

# Sematic
from sematic import CloudResolver, LocalResolver, Resolver, SilentResolver
from sematic.ee.plugins.external_resource.ray.load_testing.pipeline import (
    CollatzConfig,
    load_test_ray,
)

logger = logging.getLogger(__name__)

BAZEL_COMMAND = (
    "bazel run //sematic/ee/plugins/external_resource/ray/load_testing:__main__ --"
)
DESCRIPTION = (
    "This pipeline is used to perform load testing on the Ray integration. "
    "The arguments control the shape of the pipeline, as described in the individual "
    "help strings. "
)
CLOUD_HELP = (
    "Whether to run the resolution in the cloud, or locally. Defaults to False. "
    "Only one of --silent or --cloud are allowed."
)
SILENT_HELP = (
    "Whether to run the resolution using the SilentResolver. Defaults to False. "
    "Only one of --silent or --cloud are allowed."
)
COLLATZ_N_WORKERS_HELP = "Number of workers when doing the Collatz load test"
COLLATZ_N_TASKS_HELP = "Number of tasks to perform operations on for Collatz load test"
COLLATZ_WAIT_MINUTES_HELP = (
    "Number of minutes to wait before stopping the Collatz load test"
)
COLLATZ_MEMORY_GROWTH_FACTOR_HELP = (
    "For each Collatz task, how rapidly should memory usage grow per iteration in the "
    "task? A factor of 1.25 grows at about a rate of an extra 25% per iteration, and is "
    "enough to OOM for tasks around 100. 1.0 should be safe to not OOM."
)


def _parse_args() -> argparse.Namespace:
    """Parses the command line arguments."""
    parser = argparse.ArgumentParser(prog=BAZEL_COMMAND, description=DESCRIPTION)

    # Resolver args:
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

    args = parser.parse_args()

    return args


def _get_resolver(args: argparse.Namespace) -> Resolver:
    """Instantiates the Resolver based on the passed arguments."""
    if args.silent:
        return SilentResolver()
    if not args.cloud:
        return LocalResolver()

    return CloudResolver(
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

    args = _parse_args()
    logger.info("Command line arguments: %s", args)

    collatz_config_args = {
        arg_key.replace("collatz_", ""): arg_val
        for arg_key, arg_val in vars(args).items()
        if arg_key.startswith("collatz_")
    }
    collatz_config = CollatzConfig(**collatz_config_args)
    if collatz_config.n_workers == 0:
        collatz_config = None

    resolver = _get_resolver(args)

    future = load_test_ray(collatz_config).set(
        tags=["load-testing", "ray"],
    )

    logger.info("Invoking the pipeline...")
    result = future.resolve(resolver)
    logger.info("Pipeline result: %s", result)


if __name__ == "__main__":
    main()
