"""
This is the entry point of your pipeline.

This is where you import the pipeline function from its module and resolve it.
"""
from sematic.examples.template.pipeline import pipeline


def main():
    """
    Entry point of my pipeline.
    """
    pipeline().resolve()


if __name__ == "__main__":
    main()
