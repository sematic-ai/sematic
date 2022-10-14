# Standard Library
import logging

# Sematic
from sematic import CloudResolver
from sematic.examples.add.pipeline import pipeline

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    future = pipeline(1, 2, 3).set(
        name="Basic add example pipeline", tags=["example", "basic", "final"]
    )
    result = future.resolve(CloudResolver())

    logging.info(result)
