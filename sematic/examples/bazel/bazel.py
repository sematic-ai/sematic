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

    logger.info("Starting bazel example...")
    future = pipeline(1, 2, 3)
    sematic.CloudRunner(detach=args.detach).run(future)
