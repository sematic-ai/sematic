# Standard Library
import time

from enum import Enum, unique

# Sematic
import sematic

@unique
class Color(Enum):
    RED = "RED"
    GREEN = "GREEN"
    BLUE = "BLUE"


@sematic.func(
    inline=False,
    resource_requirements=sematic.ResourceRequirements(
        kubernetes=sematic.KubernetesResourceRequirements(
            tolerations=[
                sematic.KubernetesToleration(
                    key="foo",
                    operator=sematic.KubernetesTolerationOperator.Exists,
                    effect=sematic.KubernetesTolerationEffect.NoSchedule,
                    #toleration_seconds=42,
                )
            ],
        ),
    )
)
def add(a: float, b: float, color: Color=Color.RED) -> float:
    time.sleep(5)
    return a + b

class SomeException(Exception):
    pass

import random
import logging

@sematic.func(base_image_tag="cuda", inline=False, retry=sematic.RetrySettings(exceptions=(SomeException,), retries=15))
def add3(a: float, b: float, c: float) -> float:
    return add(add(a, b), c)


@sematic.func(inline=False)
def fail() -> float:
    return fail_nested()


@sematic.func(inline=False)
def fail_nested() -> float:
    raise ValueError("Some exception")


@sematic.func(inline=True)
def pipeline(a: float, b: float, c: float) -> float:
    #return add(add3(a, b, c), add(a, b))
    # return add(a, b)
    #return fail()
    sleep_time = 600
    return int_sum([sleep_for(sleep_time, int(time.time())) for _ in range(10)])

from typing import List

@sematic.func(inline=False)
def do_something() -> str:
    return "42"

@sematic.func(inline=False)
def sleep_for(n_seconds: int, scheduled_at: int) -> int:
    started = time.time()
    while time.time() < started + n_seconds:
        amount_slept = int(time.time() - started)
        since_schedule = int(time.time() - scheduled_at)
        print(f"Sleeping at {amount_slept}s of {n_seconds}s. Whole pipeline started {since_schedule}s ago...")
        time.sleep(1)
    return n_seconds


@sematic.func(inline=False)
def int_sum(elements: List[int]) -> float:
    return 1.0 * sum(elements)

#@sematic.func(inline=False)
#def pipeline(a: float, b: float, c: float) -> List[str]:
#    result = [do_something() for _ in range(0, 2)]
#    return result

#print(pipeline().resolve())
