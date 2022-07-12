import logging
import sematic


@sematic.func
def pipeline():
    pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting bazel example")
    future = pipeline()
    logging.info(future.id)
    future.resolve(sematic.CloudResolver())
