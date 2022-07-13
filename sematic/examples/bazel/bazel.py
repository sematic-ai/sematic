import logging
import sematic

from sematic.examples.bazel.pipeline import pipeline


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    logger.info("Starting bazel example")
    future = pipeline(1, 2)
    future.resolve(sematic.CloudResolver())
