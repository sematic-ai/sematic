# Standard library
import logging

# Glow
from glow import OfflineResolver
from glow.examples.add.calculators import pipeline


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    future = pipeline(1, 2, 3)

    result = future.resolve(OfflineResolver())

    logging.info(result)
