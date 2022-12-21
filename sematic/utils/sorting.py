# Standard Library
from typing import Dict, List, Optional

# Sematic
from sematic.utils.algorithms import breadth_first_search


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
    sorted_ids: List[Optional[str]] = []

    def visit(id_):
        sorted_ids.append(id_)

    def find_next_ids(previous_id):
        # Sorting for determinism.
        next_ids = sorted(
            element for element, deps in dependencies.items() if previous_id in deps
        )
        return next_ids

    start_nodes = [element for element, deps in dependencies.items() if deps == [None]]

    breadth_first_search(start=start_nodes, get_next=find_next_ids, visit=visit)
    return sorted_ids
