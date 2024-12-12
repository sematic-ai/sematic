"""
This is the entry point of your pipeline.

This is where you import the pipeline function from its module and resolve it.
"""

# Standard Library
import argparse

# Sematic
from sematic import LocalRunner
from sematic.examples.dynamic_graph.pipeline import pipeline


def main(ntries: int):
    """
    Entry point of my pipeline.
    """
    future = pipeline(ntries).set(
        name="Dynamic graph example", tags=["examples", "dynamic"]
    )
    LocalRunner().run(future)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ntries", default=5)

    args = parser.parse_args()

    main(args.ntries)
