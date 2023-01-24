"""
Flexible-structure pipeline meant to be used in testing.
"""
# Standard Library
import logging
import os
import random
import time
from typing import List, Optional

# Third-party
import ray

# Sematic
import sematic
from sematic.plugins.abstract_kuberay_wrapper import RayNodeConfig, SimpleRayCluster
from sematic.plugins.external_resource.ray.cluster import RayCluster
from sematic.plugins.external_resource.timed_message import TimedMessage
from sematic.resolvers.resource_requirements import ResourceRequirements

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
    logger.info(
        "Executing: add_inline(a=%s, b=%s)",
        a,
        b,
    )
    time.sleep(5)
    return a + b


@sematic.func(inline=True)
def add_inline_using_resource(a: float, b: float) -> float:
    """
    Adds two numbers and logs info about a custom resource.
    """
    with TimedMessage(
        message="some message", allocation_seconds=2, deallocation_seconds=2
    ) as timed_message:
        logger.info(
            "Executing: add(a=%s, b=%s, timed_message='%s')",
            a,
            b,
            timed_message.read_message(),
        )
        return a + b


@sematic.func(inline=False)
def add_using_resource(a: float, b: float) -> float:
    """
    Adds two numbers and logs info about a custom resource.
    """
    with TimedMessage(
        message="Some message", allocation_seconds=2, deallocation_seconds=2
    ) as timed_message:
        logger.info(
            "Executing: add(a=%s, b=%s, timed_message='%s')",
            a,
            b,
            timed_message.read_message(),
        )
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
    Raises a ValueError, without retries.
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
def do_exit(val: float, exit_code: int) -> float:
    """
    Exits execution using the specified exit code.

    The other parameter is ignored.
    """
    logger.info("Executing: do_exit(val=%s, exit_code=%s)", val, exit_code)
    time.sleep(5)
    os._exit(exit_code)
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


@sematic.func(inline=True)
def testing_pipeline(
    inline: bool = False,
    nested: bool = False,
    fan_out: int = 0,
    sleep_time: int = 0,
    should_raise: bool = False,
    raise_retry_probability: Optional[float] = None,
    oom: bool = False,
    external_resource: bool = False,
    ray_resource: bool = False,
    resource_requirements: Optional[ResourceRequirements] = None,
    cache: bool = False,
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
    sleep_time: int
        Includes a function which sleeps for the specified number of seconds, logging a
        message every second. Defaults to 0.
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
    external_resource: bool
        Whether to use an external resource. Defaults to False.
    resource_requirements: Optional[ResourceRequirements]
        If not None, includes a function that runs with the specified requirements.
        Defaults to False.
    cache: bool
        Whether to include nested functions which will have the `cache` flag activated.
        Defaults to False.
    exit_code: Optional[int]
        If not None, includes a function which will exit with the specified code.
        Defaults to None.
    external_resource: bool
        Whether to use an external resource. Defaults to False.
    ray_resource:
        If True, two numbers will be added using a Ray task that executes on
        a remote cluster.
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

    if sleep_time > 0:
        futures.append(do_sleep(initial_future, sleep_time))

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
        function = add_with_resource_requirements(initial_future, 3)
        function.set(resource_requirements=resource_requirements)
        futures.append(function)

    if cache:
        futures.append(add4_nested_cached(initial_future, 1, 2, 3))

    if exit_code is not None:
        futures.append(do_exit(initial_future, exit_code))

    if ray_resource:
        futures.append(add_with_ray(initial_future, 1.0))

    # collect all values
    result = add_all(futures) if len(futures) > 1 else futures[0]
    return result
