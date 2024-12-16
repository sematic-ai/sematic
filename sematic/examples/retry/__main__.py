# Sematic
from sematic import LocalRunner
from sematic.examples.retry.pipeline import raise_exception


if __name__ == "__main__":
    LocalRunner().run(raise_exception())
