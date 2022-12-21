# Sematic
from sematic.utils.sorting import topological_sort


def test_topological_sort():
    dependencies = {
        "A": [None],
        "B": ["A"],
        "C": ["A"],
        "D": ["C", "E"],
        "E": ["B", "A"],
    }

    assert topological_sort(dependencies) == ["A", "B", "C", "E", "D"]
