# Standard library
import logging

# Sematic
from sematic import LocalResolver
from sematic.examples.add.calculators import (  # noqa:F401
    pipeline,
    sum_list,
    using_dataclass,
)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    future = pipeline(1, 2, 3).set(
        name="Basic add example pipeline", tags=["example", "basic", "final"]
    )

    # future = sum_list([1, 2, 3, 4, 5], 0.5)

    # future = using_dataclass(dict(foo=[1, 2, 3], bar=dict(barr=[3, 4, 5])))
    result = future.resolve(LocalResolver())

    logging.info(result)
