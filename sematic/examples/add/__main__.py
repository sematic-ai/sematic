# Standard Library
import logging

# Sematic
from sematic import LocalResolver
from sematic.examples.add.pipeline import pipeline

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    future = pipeline(1, 2, 3).set(
        name="Basic add example pipeline", tags=["example", "basic", "final"]
    )
    result = future.resolve(
        LocalResolver(rerun_from="7b28ff3c190d414cb9b1524909339a4c")
    )

    logging.info(result)
