# Standard Library
from collections import deque
from typing import Callable, Dict, Hashable, List, Optional, TypeVar

T = TypeVar("T")


def breadth_first_search(
    start: List[T],
    get_next: Callable[[T], List[T]],
    visit: Callable[[T], None],
    key_func: Optional[Callable[[T], Hashable]] = None,
) -> None:
    """Start at the given element and do a breadth first traversal of the implicit graph.

    Parameters
    ----------
    start:
        The graph elements to start from.
    get_next:
        Given an element in the graph, get a list of the next elements in the graph.
    visit:
        This function will be called on each element in the graph that is reachable from
        the starting node. It will be called exactly once on each element. It will be
        called in breadth-first order.
    key_func:
        If the elements of the graph are not hashable, this should be given as a callable
        which returns a hashable value when given an element of the graph.
    """
    visited_keys = set()
    to_visit = deque(start)
    while len(to_visit) != 0:
        visiting = to_visit.popleft()
        key = visiting if key_func is None else key_func(visiting)
        if key in visited_keys:
            continue
        visit(visiting)
        visited_keys.add(key)
        to_visit.extend(get_next(visiting))


def topological_sort(
    dependencies: Dict[str, List[Optional[str]]],
) -> List[str]:
    """
    Sorts a list of strings topologically.

    Parameters
    ----------
    dependencies: Dict[str, List[Optional[str]]]
        A mapping of node to its dependencies. The root nodes have [None] as dependencies.

    Returns
    -------
    List[str]
        IDs sorted topologically.
    """
    sorted_ids: List[str] = []

    def remove_nones(li):
        return [element for element in li if element is not None]

    def visit(id_):
        sorted_ids.append(id_)

    def find_next_ids(previous_id):
        # nobody should care about this dependency anymore
        for deps in dependencies.values():
            if previous_id in deps:
                deps.remove(previous_id)

        # Sorting for determinism.
        next_ids = sorted(
            [
                element
                for element, deps in dependencies.items()
                if remove_nones(deps) == []
            ]
        )
        return next_ids

    start_nodes = [
        element for element, deps in dependencies.items() if remove_nones(deps) == []
    ]

    breadth_first_search(start=start_nodes, get_next=find_next_ids, visit=visit)
    return sorted_ids
