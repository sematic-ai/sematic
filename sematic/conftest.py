import sys
from typing import List


MAX_PY_VERSIONS = {
    # These tests depend on libraries that do not yet have
    # full support for python 3.13. Once they do, they can be added
    # back into the test suite.
    "ee/plugins/external_resource/ray/tests/test_checkpoint.py": (3, 13),
    "ee/plugins/external_resource/ray/tests/test_cluster.py": (3, 13),
    "types/types/snowflake/tests/test_snowflake_table.py": (3, 13),
    "types/types/matplotlib/tests/test_figure.py": (3, 13),
    "types/types/pandas/tests/test_dataframe.py": (3, 13),
}

collect_ignore: List[str] = []

for path, max_version in MAX_PY_VERSIONS.items():
    if sys.version_info >= max_version:
        collect_ignore.append(path)
