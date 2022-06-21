"""
This is the entry point of your pipeline.

This is where you import the pipeline function from its module and resolve it.
"""
import argparse
from sematic.examples.dynamic_graph.pipeline import pipeline


def main(ntries: int):
    """
    Entry point of my pipeline.
    """
    pipeline(ntries).set(
        name="Dynamic graph example", tags=["examples", "dynamic"]
    ).resolve()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ntries", default=5)

    args = parser.parse_args()

    main(args.ntries)
