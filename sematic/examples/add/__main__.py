# Standard Library
import logging

# Sematic
from sematic.examples.add.pipeline import pipeline, raise_exception
from sematic import CloudResolver

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    future = pipeline(1, 2, 3).set(
        name="Basic add example pipeline", tags=["example", "basic", "final"]
    )
    # result = future.resolve()

    result = raise_exception().resolve(CloudResolver(detach=False))

    logging.info(result)
