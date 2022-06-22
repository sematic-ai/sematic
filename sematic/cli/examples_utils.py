# Standard library
import os

# Sematic
from sematic.config import get_config, EXAMPLES_DIR


MIN_EXAMPLE_FILES = [
    "__main__.py",
    "__init__.py",
    "requirements.txt",
    "AUTHORS",
    "README",
]


def is_example(path: str):
    """
    Is `path` the path to an example pipeline?
    """
    base_path = os.path.join(get_config().base_dir, path)

    return all(
        os.path.exists(os.path.join(base_path, file_name))
        for file_name in MIN_EXAMPLE_FILES
    )


def all_examples():
    return [
        "{}{}".format(EXAMPLES_DIR, dir.split(EXAMPLES_DIR)[1])
        for dir, _, __ in os.walk(get_config().examples_dir)
        if is_example(dir)
    ]
