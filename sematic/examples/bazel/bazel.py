# Standard Library
import argparse
import logging

# Sematic
import sematic
from sematic.examples.bazel.pipeline import pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Bazel Example")
    parser.add_argument("--detach", default=False, action="store_true")

    args = parser.parse_args()
    max_parallel = 2

    logger.info("Starting bazel example...")
    future = pipeline(1, 2, 3).set(tags=[f"max_parallel:{max_parallel}"])
    future.resolve(sematic.CloudResolver(detach=args.detach, max_parallelism=max_parallel))
