# Standard Library
from typing import Dict, List, Optional


def topological_sort(
    dependencies: Dict[str, List[Optional[str]]],
) -> List[str]:
    """
    Sorts a list of strings topologically.

    Parameters
    ----------
    dependencies: Dict[str, List[Optional[str]]]
        A mapping of node to its dependencies. Roots has [None].
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
