"""
This is the entry point of your pipeline.

This is where you import the pipeline function from its module and run it.
"""

# Sematic
from sematic import LocalRunner
from sematic.examples.template.pipeline import pipeline


def main():
    """
    Entry point of my pipeline.
    """
    future = pipeline()
    LocalRunner().run(future)


if __name__ == "__main__":
    main()
