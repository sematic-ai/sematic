# Standard Library
from collections import deque
from typing import Callable, Hashable, List, Optional, TypeVar

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
