"""
This is the entry point for the sematic_pipeline Bazel rule.

We need to do this because we don't want to use the current worker at
//sematic/resolvers:worker we want to use the one in the wheel that the user has
installed.
"""
from sematic.resolvers.worker import wrap_main_with_logging

if __name__ == "__main__":
    wrap_main_with_logging()
