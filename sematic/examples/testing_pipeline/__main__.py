"""
Entry point for the testing pipeline.
"""
# Standard Library
import argparse
import logging
import os
import sys
from typing import Dict, Optional

# Third-party
import debugpy

# Sematic
from sematic import CloudResolver, LocalResolver, SilentResolver
from sematic.examples.testing_pipeline.pipeline import testing_pipeline
from sematic.resolvers.resource_requirements import (
    KubernetesResourceRequirements,
    ResourceRequirements,
)
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
    "Whether to run the resolution in the cloud, or locally. Defaults to False. "
    "Only one of --silent or --cloud are allowed."
)
SILENT_HELP = (
    "Whether to run the resolution using the SilentResolver. Defaults to False. "
    "Only one of --silent or --cloud are allowed."
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
    "The maximum number of Standalone Function Runs that will be allowed to be in the "
    "`SCHEDULED` state at any one time. Must be a positive integer, or None for "
    "unlimited runs. Defaults to None."
)
INLINE_HELP = (
    "Whether to include an inline function in the pipeline. Defaults to False."
)
NESTED_HELP = "Whether to include nested functions in the pipeline. Defaults to False."
NO_INPUT_HELP = "Whether to include a function that takes no input. Defaults to False."
SLEEP_HELP = (
    "If greater than zero, includes a function which sleeps for the specified number of "
    "seconds, logging a message every second. Defaults to 0."
)
SPAM_LOGS_HELP = (
    "If greater than zero, includes a function which produces the specified number of "
    "log lines at INFO level. Defaults to 0."
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
TIMEOUT_HELP = (
    "Two integers. If both ints are greater than 0, includes a "
    "sleep function whose duration is determined by the first argument and whose "
    "timeout limit is determined by the second argument. Units for both are in minutes. "
    "Defaults to `None`."
)
NESTED_TIMEOUT_HELP = (
    "Two integers. If both ints are greater than 0, includes a "
    "sleep function whose duration is determined by the first argument and whose "
    "timeout limit is determined by the second argument. Units for both are in minutes. "
    "Contrary to --timeout, this sets the timeout on an outer function and waits in an "
    "inner function. Defaults to `None`."
)
OOM_HELP = (
    "Whether to include a function that causes an Out of Memory error. "
    "Defaults to False."
)
EXTERNAL_RESOURCE_HELP = (
    "Whether to use an artificial external resource when executing some of "
    "the 'add' functions."
)
RAY_HELP = (
    "Includes a function that is executed on the specified external Ray cluster. "
    "If not provided, Ray will not be used. Defaults to None. "
    "Example: 'ray://raycluster-complete-head-svc:10001'."
)
EXPAND_SHARED_MEMORY_HELP = (
    "Whether to include a function that runs on a Kubernetes pod which uses an expanded "
    "shared memory partition. This option is added to a shared function which uses one "
    "KubernetesResourceRequirements configuration containing all the relevant specified "
    "CLI parameters. Defaults to False."
)
CACHE_HELP = (
    "The cache namespace to use for funcs whose outputs will be cached. "
    "Defaults to None, which deactivates caching."
)
IMAGES_HELP = (
    "Whether to include nested functions which will include the `Image` type in their "
    "I/O signatures. Defaults to False."
)
S3_URIS_HELP = (
    "If any values are supplied, includes a function that composes `S3Location` "
    "dataclasses for the specified URIs. Defaults to None."
)
VIRTUAL_FUNCS_HELP = (
    "Whether to explicitly include the `_make_list`, `_make_tuple`, and `_getitem` "
    "virtual functions. Defaults to False. Note: If this pipeline is invoked with any "
    "parameters, `_make_list` is automatically included at the end of the execution "
    "anyway, in order to collect all intermediate results."
)
FORK_SUBPROCESS_HELP = (
    "Includes a function that forks a subprocess, and then performs the specified "
    "action, using the specified value:\n"
    " - on 'return', the subprocess returns the specified value\n"
    " - on 'exit', the subprocess exits with the specified code\n"
    " - on 'signal', the parent process sends the specified signal to the subprocess"
)
EXIT_HELP = (
    "Includes a function which will exit with the specified code. "
    "If specified without a value, defaults to 0. Defaults to None."
)


class StoreCacheNamespace(argparse.Action):
    """Custom action to store the cache namespace string and the cache flag."""

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        setattr(namespace, "cache", True)


class AppendForkAction(argparse._AppendAction):
    """Custom action to append the fork subprocess action to perform."""

    valid_actions = {"return", "exit", "signal"}

    def __call__(self, parser, namespace, values, option_string=None):
        if (
            values is None
            or len(values) != 2
            or values[0] not in AppendForkAction.valid_actions
            or not values[1].isdigit()
            or (values[0] == "exit" and int(values[1]) < 0)
            or (values[0] == "signal" and int(values[1]) < 1)
        ):
            raise ValueError(
                f"Invalid action or value for parameter '--fork-subprocess': {values}"
            )

        normalized_values = values[0], int(values[1])

        items = getattr(namespace, self.dest) or []
        items = items[:]
        items.append(normalized_values)
        setattr(namespace, self.dest, items)


def _required_by(*args: str) -> Dict[str, bool]:
    """Syntactic sugar to specify argparse dependencies between arguments."""
    return {"required": any([arg in sys.argv for arg in args])}


def _parse_args() -> argparse.Namespace:
    """Parses the command line arguments."""
    parser = argparse.ArgumentParser(
        prog=BAZEL_COMMAND,
        description=DESCRIPTION,
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # Resolver args:
    parser.add_argument("--log-level", type=str, default="INFO", help=LOG_LEVEL_HELP)
    parser.add_argument(
        "--cloud",
        action="store_true",
        default=False,
        help=CLOUD_HELP,
        **_required_by(
            "--detach",
            "--expand-shared-memory",
            "--max-parallelism",
            "--oom",
            "--ray-resource",
        ),
    )
    parser.add_argument(
        "--silent",
        action="store_true",
        default=False,
        help=SILENT_HELP,
    )
    parser.add_argument(
        "--detach",
        action="store_true",
        default=False,
        help=DETACH_HELP,
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
        "--no-input", action="store_true", default=False, help=NO_INPUT_HELP
    )
    parser.add_argument(
        "--sleep", type=int, default=0, dest="sleep_time", help=SLEEP_HELP
    )
    parser.add_argument(
        "--spam-logs", type=int, default=0, dest="spam_logs", help=SPAM_LOGS_HELP
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
    parser.add_argument(
        "--timeout",
        nargs=2,
        type=int,
        default=None,
        dest="timeout_settings",
        help=TIMEOUT_HELP,
    )
    parser.add_argument(
        "--nested-timeout",
        nargs=2,
        type=int,
        default=None,
        dest="nested_timeout_settings",
        help=NESTED_TIMEOUT_HELP,
    )
    parser.add_argument("--oom", action="store_true", default=False, help=OOM_HELP)
    parser.add_argument(
        "--external-resource",
        action="store_true",
        default=False,
        help=EXTERNAL_RESOURCE_HELP,
    )
    parser.add_argument(
        "--expand-shared-memory",
        action="store_true",
        default=False,
        help=EXPAND_SHARED_MEMORY_HELP,
    )
    parser.add_argument(
        "--ray-resource",
        action="store_true",
        default=False,
        help=RAY_HELP,
    )
    parser.add_argument(
        "--cache-namespace",
        action=StoreCacheNamespace,
        type=str,
        default=None,
        help=CACHE_HELP,
    )
    parser.add_argument(
        "--images", action="store_true", default=False, help=IMAGES_HELP
    )
    parser.add_argument(
        "--s3-uris", type=str, default=None, nargs="+", help=S3_URIS_HELP
    )
    parser.add_argument(
        "--virtual-funcs",
        action="store_true",
        default=False,
        help=VIRTUAL_FUNCS_HELP,
    )
    parser.add_argument(
        "--fork-subprocess",
        dest="fork_actions",
        action=AppendForkAction,
        metavar=("action", "code"),
        nargs="*",
        help=FORK_SUBPROCESS_HELP,
    )
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
    if args.log_level is not None:
        args.log_level = args.log_level.upper()

    # args values validations:
    logging._checkLevel(args.log_level)

    if args.sleep_time < 0:
        raise ValueError(f"Expected '--sleep' value to be >= 0; got: {args.sleep_time}")

    if args.fan_out < 0:
        raise ValueError(f"Expected '--fan-out' value to be >= 0; got: {args.fan_out}")

    if args.silent and args.cloud:
        raise ValueError(
            "Only one of '--silent' or '--cloud' can be used, but both were specified"
        )

    resource_requirements = _get_resource_requirements(args)
    if resource_requirements is not None:
        args.resource_requirements = resource_requirements

    return args


def _get_resolver(args: argparse.Namespace) -> StateMachineResolver:
    """Instantiates the Resolver based on the passed arguments."""
    if args.silent:
        return SilentResolver()
    if not args.cloud:
        return LocalResolver(
            rerun_from=args.rerun_from, cache_namespace=args.cache_namespace
        )

    return CloudResolver(
        detach=args.detach,
        cache_namespace=args.cache_namespace,
        max_parallelism=args.max_parallelism,
        rerun_from=args.rerun_from,
    )


def _get_resource_requirements(
    args: argparse.Namespace,
) -> Optional[ResourceRequirements]:
    """Instantiates ResourceRequirements based on the passed arguments."""
    # add all new resource requirements here
    if not args.expand_shared_memory:
        return None

    k8_resource_requirements = KubernetesResourceRequirements(
        mount_expanded_shared_memory=args.expand_shared_memory
    )

    return ResourceRequirements(kubernetes=k8_resource_requirements)


def _wait_for_debugger():
    debugpy.listen(5724)

    print("Waiting for debugger to attach...")
    debugpy.wait_for_client()
    print("Debugger attached")


def main() -> None:
    if os.environ.get("DEBUGPY", None) is not None:
        _wait_for_debugger()

    args = _parse_args()
    logging.basicConfig(level=args.log_level)
    logger.info("Command line arguments: %s", args)

    effective_arg_keys = vars(args).keys() & testing_pipeline.input_types.keys()
    effective_args = {key: vars(args)[key] for key in effective_arg_keys}
    logger.info("Pipeline arguments: %s", effective_args)

    resolver = _get_resolver(args)

    future = testing_pipeline(**effective_args).set(
        name="Sematic Testing Pipeline",
        tags=["example", "testing"],
    )

    logger.info("Invoking the pipeline...")
    result = future.resolve(resolver)
    logger.info("Pipeline result: %s", result)


if __name__ == "__main__":
    main()
