# Standard Library
from typing import Callable, Dict, List, Optional


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

    def _find_next_ids(previous_ids: List[Optional[str]]):
        # Sorting for determinism.
        next_ids = sorted(
            [
                id_
                for id_, deps in dependencies.items()
                if id_ not in previous_ids
                and all(dependency in previous_ids for dependency in deps)
            ]
        )

        if len(next_ids) == 0:
            return []

        return next_ids + _find_next_ids(previous_ids + next_ids)  # type: ignore

    return _find_next_ids([None])


def breadth_first(
    layers: Dict[Optional[str], List[str]],
    layer_sorter: Callable[[List[str]], List[str]] = sorted,
) -> List[str]:
    """
    Breadth-first sorting.

    Parameters
    ----------
    layers: Dict[Optional[str], List[str]]
        A mapping of parent node to list of child nodes.
    layer_sorter: Callable[[List[str]], List[str]]
        A sorter to sort ids within a given layer.

    Returns
    -------
    List[str]
        IDs ordered breadth first and according to layer_sorter with a given
        layer.
    """
    ids: List[str] = []

    def _add_layer_ids(parent_id: Optional[str]):
        layer_ids: List[str] = layers.get(parent_id, [])

        ordered_layer_ids = layer_sorter(layer_ids)
        ids.extend(ordered_layer_ids)

        for id_ in ordered_layer_ids:
            _add_layer_ids(id_)

    _add_layer_ids(None)

    return ids
