# Sematic
from sematic.utils.algorithms import breadth_first_search, topological_sort


def test_breadth_first_search():
    # represent this structure:
    #
    #  "a"  "b"  "c"
    #     \ / \    \
    #     "d" "e"  "f"
    #     /    | \  / \
    #    "g"  "h" "i"  |
    #      \   |  /____|
    #        "j"
    graph = {
        "a": [],
        "b": [],
        "c": [],
        "d": ["a", "b"],
        "e": ["b"],
        "f": ["c"],
        "g": ["d"],
        "h": ["e"],
        "i": ["e", "f"],
        "j": ["g", "h", "f", "i"],
    }

    def get_next(val):
        return graph[val]

    visited = []

    def visit(val):
        visited.append(val)

    breadth_first_search(
        start=["j"],
        get_next=get_next,
        visit=visit,
    )

    assert len(visited) == len(graph.keys())
    assert visited[0] == "j"
    assert set(visited[1:5]) == {"g", "h", "i", "f"}
    assert set(visited[5:7]) == {"d", "e"}
    assert set(visited[7:10]) == {"a", "b", "c"}

    visited = []
    breadth_first_search(
        start=["g", "h", "i"],
        get_next=get_next,
        visit=visit,
    )
    assert set(visited[0:3]) == {"g", "h", "i"}
    assert set(visited[3:6]) == {"d", "e", "f"}
    assert set(visited[6:9]) == {"a", "b", "c"}


def test_breadth_first_search_key_func():
    """Test a case where the elements in the traversal are not hashable.

    If the elements are not hashable, then a key function will be required
    to get a hashable value from the elements.
    """

    def get_key(element) -> str:
        if 3 in element:
            return "numbers"
        elif "a" in element:
            return "characters"
        elif True in element:
            return "bools"
        elif None in element:
            return "nones"
        raise AssertionError("Should not reach here")

    # represent this graph structure:
    #         {1, 2, 3}
    #        /           \
    #  {True, False} {"a", "b", "c"}
    #        \            /
    #           {None}
    graph = {
        "nones": [{True, False}, {"a", "b", "c"}],
        "bools": [{1, 2, 3}],
        "characters": [{1, 2, 3}],
        "numbers": [],
    }

    def get_next(element):
        k = get_key(element)
        return graph[k]

    visited = []

    def visit(element):
        visited.append(element)

    breadth_first_search(
        start=[{None}],
        get_next=get_next,
        visit=visit,
        key_func=get_key,
    )

    assert len(visited) == len(graph.keys())
    assert visited[0] == {None}
    if visited[1] == {True, False}:
        assert visited[2] == {"a", "b", "c"}
    else:
        assert visited[1:3] == [{"a", "b", "c"}, {True, False}]
    assert visited[3] == {1, 2, 3}


def test_topological_sort():
    # Represents:
    #       A
    #     / | \
    #    C  B  |
    #    |  \  |
    #     \    E
    #      \   |
    #        D
    dependencies = {
        "A": [None],
        "B": ["A"],
        "C": ["A"],
        "D": ["C", "E"],
        "E": ["B", "A"],
    }

    assert topological_sort(dependencies) == ["A", "B", "C", "E", "D"]
