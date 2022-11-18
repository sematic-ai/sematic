"""
Entry point for the testing pipeline.
"""
# Standard Library
import argparse
import logging
import sys
from typing import Dict

# Sematic
from sematic import CloudResolver, LocalResolver
from sematic.examples.testing_pipeline.pipeline import testing_pipeline
from sematic.resolvers.state_machine_resolver import StateMachineResolver

logger = logging.getLogger(__name__)

BAZEL_COMMAND = "bazel run //sematic/examples/testing_pipeline:__main__ --"
DESCRIPTION = (
    "This is the Sematic Testing Pipeline. "
    "It is used to test the behavior of the Server and of the Resolver. "
    "The arguments control the shape of the pipeline, as described in the individual "
    "help strings. "
    "Some of the arguments have dependencies on other arguments, and missing values will "
    "be reported to the user. "
    "At the end of the pipeline execution, the individual future outputs are collected "
    "in a future list and reduced."
)
LOG_LEVEL_HELP = "The log level for the pipeline and Resolver. Defaults to INFO."
CLOUD_HELP = (
    "Whether to run the resolution in the cloud, or locally. Defaults to False."
)
DETACH_HELP = (
    "When in `cloud` mode, whether to detach the execution of the driver job and have it "
    "run on the remote cluster. This is the so called `fire-and-forget` mode. The shell "
    "prompt will return as soon as the driver job as been submitted. Defaults to False."
)
RERUN_FROM_HELP = (
    "The id of a run to rerun as part of a new pipeline resolution. This will copy the "
    "previous resolution, while invalidating any failed runs, this specified run, and "
    "any of its downstream runs, and then continue the resolution from there. Defaults "
    "to None."
)
MAX_PARALLELISM_HELP = (
    "The maximum number of non-inlined runs that will be allowed to be in the "
    "`SCHEDULED` state at any one time. Must be a positive integer, or None for "
    "unlimited runs. Defaults to None."
)
INLINE_HELP = (
    "Whether to include an inline function in the pipeline. Defaults to False."
)
NESTED_HELP = "Whether to include nested functions in the pipeline. Defaults to False."
SLEEP_HELP = (
    "Includes a function which sleeps for the specified number of seconds, logging a "
    "message every second. Defaults to 0."
)
FAN_OUT_HELP = (
    "How many dynamically-generated functions to add in parallel. Defaults to 0."
)
RAISE_HELP = (
    "Whether to include a function that raises a ValueError, without retries. "
    "Defaults to False."
)
RAISE_RETRY_HELP = (
    "Includes a function which raises a ValueError with the given probability, "
    "with a total of 10 retries. If specified without a value, defaults to 0.5, "
    "meaning a cumulative probability of complete failure of 0.5 ** 11 = 0.00048828125."
)
OOM_HELP = (
    "Whether to include a function that causes an Out of Memory error. "
    "Defaults to False."
)
EXIT_HELP = (
    "Includes a function which will exit with the specified code. "
    "If specified without a value, defaults to 0."
)


def _required_by(*args: str) -> Dict[str, bool]:
    """Syntactic sugar to specify argparse dependencies between arguments."""
    return {"required": any([arg in sys.argv for arg in args])}


def _parse_args() -> argparse.Namespace:
    """Parses the command line arguments."""
    parser = argparse.ArgumentParser(prog=BAZEL_COMMAND, description=DESCRIPTION)

    # Resolver args:
    parser.add_argument("--log-level", type=str, default="INFO", help=LOG_LEVEL_HELP)
    parser.add_argument(
        "--cloud",
        action="store_true",
        default=False,
        help=CLOUD_HELP,
        **_required_by("--detach", "--max-parallelism", "--oom"),
    )
    parser.add_argument(
        "--detach",
        action="store_true",
        default=False,
        help=DETACH_HELP,
        **_required_by("--rerun-from"),
    )
    parser.add_argument(
        "--rerun-from",
        type=str,
        default=None,
        help=RERUN_FROM_HELP,
    )
    parser.add_argument(
        "--max-parallelism",
        type=int,
        default=None,
        help=MAX_PARALLELISM_HELP,
    )

    # Pipeline args:
    parser.add_argument(
        "--inline", action="store_true", default=False, help=INLINE_HELP
    )
    parser.add_argument(
        "--nested", action="store_true", default=False, help=NESTED_HELP
    )
    parser.add_argument(
        "--sleep", type=int, default=0, dest="sleep_time", help=SLEEP_HELP
    )
    parser.add_argument("--fan-out", type=int, default=0, help=FAN_OUT_HELP)
    parser.add_argument(
        "--raise",
        action="store_true",
        dest="should_raise",
        default=False,
        help=RAISE_HELP,
    )
    parser.add_argument(
        "--raise-retry",
        type=float,
        nargs="?",
        const=0.5,
        default=None,
        dest="raise_retry_probability",
        help=RAISE_RETRY_HELP,
    )
    parser.add_argument("--oom", action="store_true", default=False, help=OOM_HELP)
    parser.add_argument(
        "--exit",
        type=int,
        nargs="?",
        const=0,
        default=None,
        dest="exit_code",
        help=EXIT_HELP,
    )

    args = parser.parse_args()

    # args values validations:
    logging._checkLevel(args.log_level)

    if args.sleep_time < 0:
        raise ValueError(f"Expected '--sleep' value to be >= 0; got: {args.sleep_time}")

    if args.fan_out < 0:
        raise ValueError(f"Expected '--fan-out' value to be >= 0; got: {args.fan_out}")

    return args


def _get_resolver(args: argparse.Namespace) -> StateMachineResolver:
    """Instantiates the Resolver based on the passed arguments."""
    if not args.cloud:
        return LocalResolver(rerun_from=args.rerun_from)

    return CloudResolver(
        detach=args.detach,
        max_parallelism=args.max_parallelism,
        rerun_from=args.rerun_from,
    )


def main() -> None:
    args = _parse_args()
    logging.basicConfig(level=args.log_level)
    logger.info("Command line arguments: %s", args)

    effective_arg_keys = vars(args).keys() & testing_pipeline.input_types.keys()
    effective_args = {key: vars(args)[key] for key in effective_arg_keys}
    logger.info("Pipeline arguments: %s", effective_args)

    resolver = _get_resolver(args)
    future = testing_pipeline(**effective_args).set(
        name="Sematic Testing Pipeline", tags=["example", "testing"]
    )

    logger.info("Invoking the pipeline...")
    result = future.resolve(resolver)
    logger.info("Pipeline result: %s", result)


if __name__ == "__main__":
    main()
