"""
Entry point for the testing pipeline.
"""
# Standard Library
import argparse
import logging
import os
import sys
from typing import Dict

# Third-party
import debugpy

# Sematic
from sematic import CloudRunner, LocalRunner, SilentRunner, api_client
from sematic.examples.testing_pipeline.pipeline import testing_pipeline
from sematic.resolvers.resource_requirements import (
    KubernetesResourceRequirements,
    ResourceRequirements,
)
from sematic.runners.state_machine_runner import StateMachineRunner

logger = logging.getLogger(__name__)

BAZEL_COMMAND = "bazel run //sematic/examples/testing_pipeline:__main__ --"

DESCRIPTION = (
    "This is the Sematic Testing Pipeline. "
    "It is used to test the behavior of the Server and of the Runner. "
    "The arguments control the shape of the pipeline, as described in the individual "
    "help strings. "
    "Some of the arguments have dependencies on other arguments, and missing values will "
    "be reported to the user. "
    "At the end of the pipeline execution, the individual future outputs are collected "
    "in a future list and reduced."
)

LOG_LEVEL_HELP = "The log level for the pipeline and Runner. Defaults to INFO."
CLOUD_HELP = (
    "Whether to run the pipeline in the cloud, or locally. Defaults to False. "
    "Only one of --silent or --cloud are allowed."
)
BLOCK_HELP = (
    "Whether to block until the run is finished. If true, will print the run output "
    "upon completion."
)
SILENT_HELP = (
    "Whether to run the pipeline using the SilentRunner. Defaults to False. "
    "Only one of --silent or --cloud are allowed."
)
DETACH_HELP = (
    "When in `cloud` mode, whether to detach the execution of the driver job and have it "
    "run on the remote cluster. This is the so called `fire-and-forget` mode. The shell "
    "prompt will return as soon as the driver job as been submitted. Defaults to False."
)
RERUN_FROM_HELP = (
    "The id of a run to rerun as part of a new pipeline run. This will copy the "
    "previous pipeline run, while invalidating any failed runs, this specified run, and "
    "any of its downstream runs, and then continue the pipeline from there. Defaults "
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
RANDOM_HELP = (
    "Whether to include a function that adds a random number. Defaults to False."
)
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
MOUNT_HOST_PATH_HELP = (
    "Includes a function that runs on a Kubernetes pod which mounts the specified "
    "underlying node directory path to the specified pod path, as a Kubernetes "
    '"hostPath" volume configuration.'
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
COUNT_LETTERS_HELP = (
    "If not None, includes a function which counts the number of letters in this string. "
    "Defaults to None."
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
CUSTOM_RUNNER_RESOURCES_HELP = (
    "Specifies custom resources for the CloudRunner. When used, a hard-coded "
    "custom resource config will be used."
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


class AppendHostPathAction(argparse._AppendAction):
    """Custom action to append a Kubernetes "hostPath" volume mount configuration."""

    def __call__(self, parser, namespace, values, option_string=None):
        if values is None or len(values) != 2:
            raise ValueError(
                f"Invalid paths for parameter '--mount-host-path': {values}"
            )

        items = getattr(namespace, self.dest) or []
        items = items[:]
        items.append(values)
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

    # Runner args:
    parser.add_argument("--log-level", type=str, default="INFO", help=LOG_LEVEL_HELP)
    parser.add_argument(
        "--cloud",
        action="store_true",
        default=False,
        help=CLOUD_HELP,
        **_required_by(
            "--detach",
            "--expand-shared-memory",
            "--mount-host-path",
            "--max-parallelism",
            "--oom",
            "--ray-resource",
            "--custom-runner-resources",
        ),
    )
    parser.add_argument(
        "--silent",
        action="store_true",
        default=False,
        help=SILENT_HELP,
    )
    parser.add_argument(
        "--block",
        action="store_true",
        default=False,
        help=BLOCK_HELP,
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
        "--random", action="store_true", default=False, help=RANDOM_HELP
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
        "--mount-host-path",
        dest="mount_host_paths",
        action=AppendHostPathAction,
        metavar=("node_path", "pod_mount_path"),
        nargs="*",
        help=MOUNT_HOST_PATH_HELP,
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
        "--count-letters",
        type=str,
        default=None,
        dest="count_letters_string",
        help=COUNT_LETTERS_HELP,
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
    parser.add_argument(
        "--custom-runner-resources",
        action="store_true",
        default=False,
        help=CUSTOM_RUNNER_RESOURCES_HELP,
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

    return args


def _get_runner(args: argparse.Namespace) -> StateMachineRunner:
    """Instantiates the Runner based on the passed arguments."""
    if args.silent:
        return SilentRunner()
    if not args.cloud:
        return LocalRunner(
            rerun_from=args.rerun_from, cache_namespace=args.cache_namespace
        )

    extra_kwargs = dict()
    if args.custom_runner_resources:
        extra_kwargs["resources"] = ResourceRequirements(
            kubernetes=KubernetesResourceRequirements(
                requests={"memory": "3Gi"},
                annotations={
                    "allowed-annotation-1": "42",
                    "allowed-annotation-2": "foo",
                    "forbidden-annotation": "bad-wolf",
                },
                labels={
                    "allowed-label-1": "43",
                    "allowed-label-2": "yo",
                    "forbidden-label": "1337-hax",
                },
            )
        )
    return CloudRunner(
        detach=args.detach,
        cache_namespace=args.cache_namespace,
        max_parallelism=args.max_parallelism,
        rerun_from=args.rerun_from,
        **extra_kwargs,
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
    logging.basicConfig(level=args.log_level)
    logger.info("Command line arguments: %s", args)

    effective_arg_keys = vars(args).keys() & testing_pipeline.input_types.keys()
    effective_args = {key: vars(args)[key] for key in effective_arg_keys}
    logger.info("Pipeline arguments: %s", effective_args)

    runner = _get_runner(args)

    future = testing_pipeline(**effective_args).set(
        name="Sematic Testing Pipeline",
        tags=["example", "testing"],
    )

    logger.info("Invoking the pipeline...")
    result = runner.run(future)
    logger.info("Pipeline result: %s", result)

    if not args.block:
        return

    if args.silent:
        # no need to actually wait; the runner.run was blocking.
        run_output = result
    else:
        logger.info("Blocking to wait for run...")
        api_client.block_on_run(future.id, cancel_on_exit=True)
        run_output = api_client.get_run_output(future.id)

    logger.info("Run output: %s", run_output)


if __name__ == "__main__":
    main()
