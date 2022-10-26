# Sematic
from sematic.utils.sorting import breadth_first, topological_sort


def test_topological_sort():
    dependencies = {
        "A": [None],
        "B": ["A"],
        "C": ["A"],
        "D": ["C", "E"],
        "E": ["B", "A"],
    }

    assert topological_sort(dependencies) == ["A", "B", "C", "E", "D"]


def test_breadth_first():
    layers = {None: ["A", "B"], "A": ["C", "D"], "B": ["E", "F"], "D": ["G", "H"]}

    assert breadth_first(layers) == ["A", "B", "C", "D", "G", "H", "E", "F"]
