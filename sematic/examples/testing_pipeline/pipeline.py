"""
Flexible-structure pipeline meant to be used in testing.
"""
# Standard Library
import logging
import os
import random
import sys
import time
from typing import Dict, List, Optional, Tuple

# Third-party
import ray

# Sematic
import sematic
from sematic.calculator import _make_tuple
from sematic.ee.ray import RayCluster, RayNodeConfig, SimpleRayCluster
from sematic.plugins.external_resource.timed_message import TimedMessage
from sematic.resolvers.resource_requirements import ResourceRequirements
from sematic.types import Image, S3Location
from sematic.types.serialization import get_json_encodable_summary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@sematic.func(inline=False)
def add(a: float, b: float) -> float:
    """
    Adds two numbers.
    """
    logger.info("Executing: add(a=%s, b=%s)", a, b)
    time.sleep(5)
    return a + b


@sematic.func(inline=False)
def add_with_ray(a: float, b: float) -> float:
    """
    Adds two numbers, using a Ray cluster.
    """
    logger.info("Executing: add_with_ray(a=%s, b=%s)", a, b)
    with RayCluster(
        config=SimpleRayCluster(
            n_nodes=1, node_config=RayNodeConfig(cpu=1, memory_gb=2)
        )
    ):
        result = ray.get([add_ray_task.remote(a, b)])[0]
    logger.info("Result from ray for %s + %s: %s", a, b, result)
    return result


@ray.remote
def add_ray_task(x, y):
    # create new logger due to this:
    # https://stackoverflow.com/a/55286452/2540669
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Adding from Ray: %s, %s", x, y)
    return x + y


@sematic.func(inline=True)
def add_inline(a: float, b: float) -> float:
    """
    Adds two numbers inline.
    """
    logger.info("Executing: add_inline(a=%s, b=%s)", a, b)
    time.sleep(5)
    return a + b


@sematic.func(inline=True)
def add_inline_using_resource(a: float, b: float) -> float:
    """
    Adds two numbers and logs info about a custom resource.
    """
    logger.info("Executing: add_inline_using_resource(a=%s, b=%s)", a, b)

    with TimedMessage(
        message="some message", allocation_seconds=2, deallocation_seconds=2
    ) as timed_message:

        logger.info(
            "Adding inline with timed_message='%s'", timed_message.read_message()
        )
        time.sleep(5)
        return a + b


@sematic.func(inline=False)
def add_using_resource(a: float, b: float) -> float:
    """
    Adds two numbers and logs info about a custom resource.
    """
    logger.info("Executing: add_using_resource(a=%s, b=%s)", a, b)

    with TimedMessage(
        message="Some message", allocation_seconds=2, deallocation_seconds=2
    ) as timed_message:

        logger.info("Adding with timed_message='%s'", timed_message.read_message())
        time.sleep(5)
        return a + b


@sematic.func(inline=False)
def add_with_resource_requirements(a: float, b: float) -> float:
    """
    Adds two numbers with ResourceRequirements.
    """
    # Disclaimer: Does not come with ResourceRequirements!
    # You need to specify your own by doing:
    #   function = add_with_resource_requirements(...)
    #   function.set(resource_requirements=my_resource_requirements)
    logger.info("Executing: add_with_resource_requirements(a=%s, b=%s)", a, b)
    time.sleep(5)
    return a + b


@sematic.func(inline=False)
def add2_nested(a: float, b: float) -> float:
    """
    Adds two numbers using a nested structure.
    """
    logger.info("Executing: add2_nested(a=%s, b=%s)", a, b)
    return add(a, b)


@sematic.func(inline=False)
def add4_nested(a: float, b: float, c: float, d: float) -> float:
    """
    Adds four numbers using a nested structure.
    """
    logger.info("Executing: add4_nested(a=%s, b=%s, c=%s, d=%s)", a, b, c, d)
    return add2_nested(add2_nested(a, b), add2_nested(c, d))


@sematic.func(inline=False)
def do_no_input() -> float:
    """
    Returns a number without taking any inputs.
    """
    logger.info("Executing: do_no_input()")
    time.sleep(5)
    return 7


@sematic.func(inline=True, cache=True)
def add_inline_cached(a: float, b: float) -> float:
    """
    Adds two numbers inline, attempting to source the value from the cache.
    """
    logger.info("Executing: add_inline_cached(a=%s, b=%s)", a, b)
    time.sleep(5)
    return a + b


@sematic.func(inline=False, cache=True)
def add2_nested_cached(a: float, b: float) -> float:
    """
    Adds two numbers using a nested structure, attempting to source the value from the
    cache.
    """
    logger.info("Executing: add2_nested_cached(a=%s, b=%s)", a, b)
    return add_inline_cached(a, b)


@sematic.func(inline=False, cache=True)
def add4_nested_cached(a: float, b: float, c: float, d: float) -> float:
    """
    Adds four numbers using a nested structure, attempting to source the value from the
    cache.
    """
    logger.info("Executing: add4_nested_cached(a=%s, b=%s, c=%s, d=%s)", a, b, c, d)
    return add2_nested_cached(add2_nested_cached(a, b), add2_nested_cached(c, d))


@sematic.func(inline=False)
def add_all(values: List[float]) -> float:
    """
    Adds all the numbers in the list.
    """
    logger.info("Executing: add_all(values=%s)", values)
    sum = 0
    for val in values:
        sum += val
    return sum


@sematic.func(inline=False)
def add_fan_out(val: float, fan_out: int) -> float:
    """
    Adds the specified number of dynamically-generated functions in parallel.
    """
    logger.info("Executing: add_fan_out(val=%s, fan_out=%s)", val, fan_out)
    futures = []
    for i in range(fan_out):
        futures.append(add(val, i))
    return add_all(futures)


@sematic.func(inline=False)
def do_sleep(val: float, sleep_time: int) -> float:
    """
    Sleeps for the specified number of seconds, in 1-second stretches, logging an INFO
    message after each stretch.
    """
    logger.info("Executing: do_sleep(val=%s, sleep=%s)", val, sleep_time)
    curr_time = time.time()
    stop_time = curr_time + sleep_time

    while curr_time < stop_time:
        logger.info("do_sleep has %s more seconds to sleep", stop_time - curr_time)
        time.sleep(1)
        curr_time = time.time()

    logger.info("do_sleep is done sleeping!")
    return val


@sematic.func(inline=False)
def do_spam_logs(val: float, log_lines: int) -> float:
    """
    Logs the indicated number of INFO messages.
    """
    logger.info("Executing: do_spam_logs(val=%s, log_lines=%s)", val, log_lines)

    for i in range(1, log_lines + 1):
        logger.info("[%s] The quick brown fox jumps over the lazy dog.", i)

    return val


@sematic.func(inline=False)
def do_oom(val: float) -> float:
    """
    Causes an Out of Memory error.
    """
    logger.info("Executing: do_oom(val=%s)", val)
    time.sleep(5)
    m = []
    while True:
        m.append(" " * 2**10)
    return val


@sematic.func(inline=False)
def do_raise(val: float) -> float:
    """
    Raises a ValueError, without retries.
    """
    logger.info("Executing: do_raise(val=%s)", val)
    time.sleep(5)
    raise ValueError("test error")


@sematic.func(
    inline=False, retry=sematic.RetrySettings(exceptions=(ValueError,), retries=10)
)
def do_retry(val: float, failure_probability: float = 0.5) -> float:
    """
    Raises a ValueError with the given probability, with a total of 10 retries.
    """
    logger.info(
        "Executing: do_retry(val=%s, failure_probability=%s)", val, failure_probability
    )
    time.sleep(5)
    if random.random() < failure_probability:
        raise ValueError("test retriable exception")
    return val


@sematic.func(inline=False)
def load_image() -> Image:
    """
    Loads and returns an `Image`.
    """
    logger.info("Executing: load_image()")
    time.sleep(5)
    return Image.from_file("sematic/examples/testing_pipeline/resources/sammy.png")


@sematic.func(inline=False)
def explode_image(
    val: float, image: Image
) -> Tuple[float, Image, List[Image], Dict[str, Image]]:
    """
    Takes an `Image` and returns various data structures containing it.
    """
    logger.info(
        "Executing: explode_image(val=%s, image=%s)",
        val,
        get_json_encodable_summary(image, Image)[0],
    )
    time.sleep(5)
    return val, image, [image, image], {"the_image": image}


@sematic.func(inline=False)
def do_image_io(val: float) -> float:
    """
    Internally uses functions that pass around `Image` objects in their I/O signatures.
    """
    logger.info("Executing: do_image_io(val=%s)", val)
    image_tuple = explode_image(val, load_image())
    return add(1, image_tuple[0])


@sematic.func(inline=False)
def compose_s3_locations(
    val: float, s3_uris: List[str]
) -> Tuple[float, List[S3Location]]:
    """
    Composes `S3Location` dataclasses for the specified URIs.
    """
    logger.info("Executing: compose_s3_locations(val=%s, s3_uris=%s)", val, s3_uris)
    time.sleep(5)
    s3_locations = list(map(S3Location.from_uri, s3_uris))
    return val, s3_locations


@sematic.func(inline=False)
def do_s3_locations(val: float, s3_uris: List[str]) -> float:
    """
    Internally uses a function that composes `S3Location` dataclasses for the specified
    URIs.
    """
    logger.info("Executing: do_s3_locations(val=%s, s3_uris=%s)", val, s3_uris)
    location_tuple = compose_s3_locations(val, s3_uris)
    return add(1, location_tuple[0])


@sematic.func(inline=False)
def do_virtual_funcs(a: float, b: float, c: float) -> float:
    """
    Adds three numbers while explicitly including _make_tuple, _make_list, and _getitem.
    """
    logger.info("Executing: do_virtual_funcs(a=%s, b=%s, c=%s)", a, b, c)
    time.sleep(5)
    d, e, f = _make_tuple(Tuple[float, float, float], (a, b, c))
    return add_all([d, e, f])


@sematic.func(inline=False)
def fork_subprocess(val: float, action: str, code: int) -> float:
    """
    Forks a subprocess, and then performs the specified action, using the specified value:
     - on 'return', the subprocess returns the specified value
     - on 'exit', the subprocess exits with the specified code
     - on 'signal', the parent process sends the specified signal to the subprocess
    """
    logger.info(
        "Executing: fork_subprocess(val=%s, action=%s, code=%s)", val, action, code
    )
    time.sleep(5)

    subprocess_pid = os.fork()

    if subprocess_pid == 0:
        # in this branch we are in the subprocess
        my_pid = os.getpid()
        logger.info("Subprocess %s has started", my_pid)

        if action == "return":
            logger.info("Subprocess %s is returning: %s", my_pid, code)
            return code

        if action == "exit":
            logger.info("Subprocess %s is exiting: %s", my_pid, code)
            sys.exit(code)

        logger.info("Subprocess %s is sleeping...", my_pid)
        time.sleep(100000)

    # from here on we are in the parent
    time.sleep(5)

    if action == "signal":
        logger.info("Sending signal %s to subprocess %s...", code, subprocess_pid)
        os.kill(subprocess_pid, code)

    os.waitpid(subprocess_pid, 0)
    logger.info("Parent is done waiting on the subprocess")

    return val


@sematic.func(inline=False)
def do_exit(val: float, exit_code: int) -> float:
    """
    Exits execution using the specified exit code.

    The other parameter is ignored.
    """
    logger.info("Executing: do_exit(val=%s, exit_code=%s)", val, exit_code)
    time.sleep(5)
    os._exit(exit_code)
    return val


@sematic.func(inline=True)
def testing_pipeline(
    inline: bool = False,
    nested: bool = False,
    no_input: bool = False,
    fan_out: int = 0,
    sleep_time: int = 0,
    spam_logs: int = 0,
    should_raise: bool = False,
    raise_retry_probability: Optional[float] = None,
    oom: bool = False,
    external_resource: bool = False,
    ray_resource: bool = False,
    resource_requirements: Optional[ResourceRequirements] = None,
    cache: bool = False,
    images: bool = False,
    s3_uris: Optional[List[str]] = None,
    virtual_funcs: bool = False,
    fork_actions: Optional[List[Tuple[str, int]]] = None,
    exit_code: Optional[int] = None,
) -> float:
    """
    The root function of the testing pipeline.

    Its parameters control the actual shape of the pipeline, according to testing needs.

    Parameters
    ----------
    inline: bool
        Whether to include inline functions in the pipeline. Defaults to False.
    nested: bool
        Whether to include nested functions in the pipeline. Defaults to False.
    no_input: bool
        Whether to include a function that takes no input. Defaults to False.
    sleep_time: int
        If greater than zero, includes a function which sleeps for the specified number of
        seconds, logging a message every second. Defaults to 0.
    spam_logs: int
        If greater than zero, includes a function which produces the specified number of
        log lines at INFO level. Defaults to 0.
    fan_out: int
        How many dynamically-generated functions to add in parallel. Defaults to 0.
    should_raise: bool
        Whether to include a function that raises a ValueError, without retries.
        Defaults to False.
    raise_retry_probability: Optional[float]
        If not None, includes a function which raises a ValueError with the given
        probability, with a total of 10 retries. Defaults to None.
    oom: bool
        Whether to include a function that causes an Out of Memory error.
        Defaults to False.
    resource_requirements: Optional[ResourceRequirements]
        If not None, includes a function that runs with the specified requirements.
        Defaults to False.
    external_resource: bool
        Whether to use an external resource. Defaults to False.
    ray_resource:
        If True, two numbers will be added using a Ray task that executes on
        a remote cluster.
    cache: bool
        Whether to include nested functions which will have the `cache` flag activated.
        Defaults to False.
    images: bool
        Whether to include nested functions which will include the `Image` type in their
        I/O signatures. Defaults to False.
    s3_uris: Optional[List[str]]
        If non-empty, includes a function that composes `S3Location` dataclasses for the
        specified URIs. Defaults to None.
    virtual_funcs: bool
        Whether to include the `_make_list`, `_make_tuple`, and `_getitem` virtual
        functions. Defaults to False.
    fork_actions: Optional[List[Tuple[str, int]]]
        For each entry, includes a function that forks a subprocess, and then performs the
        specified action, using the specified value:
         - on 'return', the subprocess returns the specified value
         - on 'exit', the subprocess exits with the specified code
         - on 'signal', the parent process sends the specified signal to the subprocess
    exit_code: Optional[int]
        If not None, includes a function which will exit with the specified code.
        Defaults to None.

    Returns
    -------
    float
        A token value that results from adding the outputs of all employed funcs.
    """
    # have an initial function whose output is used as inputs by all other functions
    # this staggers the rest of the functions and allows the user a chance to monitor and
    # visualize the unfolding execution

    initial_future = add(1, 2)
    futures = [initial_future]

    if inline:
        futures.append(add_inline(initial_future, 3))

    if nested:
        futures.append(add4_nested(initial_future, 1, 2, 3))

    if no_input:
        futures.append(do_no_input())

    if sleep_time > 0:
        futures.append(do_sleep(initial_future, sleep_time))

    if spam_logs > 0:
        futures.append(do_spam_logs(initial_future, spam_logs))

    if fan_out > 0:
        futures.append(add_fan_out(initial_future, fan_out))

    if should_raise:
        futures.append(do_raise(initial_future))

    if raise_retry_probability:
        futures.append(do_retry(initial_future))

    if oom:
        futures.append(do_oom(initial_future))

    if external_resource:
        futures.append(add_using_resource(initial_future, 1.0))
        futures.append(add_inline_using_resource(initial_future, 1.0))

    if resource_requirements is not None:
        future = add_with_resource_requirements(initial_future, 3)
        future.set(resource_requirements=resource_requirements)
        futures.append(future)

    if cache:
        futures.append(add4_nested_cached(initial_future, 1, 2, 3))

    if images:
        futures.append(do_image_io(initial_future))

    if s3_uris is not None and len(s3_uris) > 0:
        futures.append(do_s3_locations(initial_future, s3_uris))

    if virtual_funcs:
        futures.append(do_virtual_funcs(initial_future, 2, 3))

    if ray_resource:
        futures.append(add_with_ray(initial_future, 1.0))

    if fork_actions is not None:
        for action, value in fork_actions:
            future = fork_subprocess(initial_future, action, value)
            future.set(name=f"fork_subprocess[{action}={value}]")
            futures.append(future)

    if exit_code is not None:
        futures.append(do_exit(initial_future, exit_code))

    # collect all values
    result = add_all(futures) if len(futures) > 1 else futures[0]
    return result
