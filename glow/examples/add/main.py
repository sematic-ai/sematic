# Standard library
import logging

# Glow
from glow import OfflineResolver
from glow.examples.add.calculators import pipeline, sum_list


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    future = pipeline(1, 2, 3).set(
        name="Basic add example pipeline", tags=["example", "basic", "final"]
    )

    future = sum_list([1, 2, 3, 4, 5], 0.5)
    result = future.resolve(OfflineResolver())

    logging.info(result)
