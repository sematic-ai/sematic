# Standard Library
import collections
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, OrderedDict, Tuple

# Sematic
from sematic.abstract_future import AbstractFuture, FutureState
from sematic.db.models.artifact import Artifact
from sematic.db.models.edge import Edge
from sematic.db.models.factories import get_artifact_value
from sematic.db.models.run import Run
from sematic.storage import Storage
from sematic.utils.memoized_property import make_cache_name, memoized_property


@dataclass
class Graph:

    runs: List[Run]
    edges: List[Edge]
    artifacts: List[Artifact]
    parent_id: Optional[str] = None

    def _populate_run_mappings(self):
        _runs_by_id: Dict[str, Run] = {}
        _runs_by_parent_ids: Dict[Optional[str], List[Run]] = defaultdict(list)

        for run in self.runs:
            _runs_by_id[run.id] = run
            _runs_by_parent_ids[run.parent_id].append(run)

        setattr(self, make_cache_name("runs_by_id"), _runs_by_id)
        setattr(self, make_cache_name("runs_by_parent_id"), _runs_by_parent_ids)

    @memoized_property
    def runs_by_id(self) -> Dict[str, Run]:
        self._populate_run_mappings()
        return self.runs_by_id

    @memoized_property
    def runs_by_parent_id(self) -> Dict[Optional[str], List[Run]]:
        self._populate_run_mappings()
        return self.runs_by_parent_id

    def _populate_edge_mappings(self):
        _edges_by_destination_id: Dict[str, List[Edge]] = defaultdict(list)

        _edges_by_source_id: Dict[str, List[Edge]] = defaultdict(list)

        _edges_by_id: Dict[str, Edge] = {}

        for edge in self.edges:
            _edges_by_id[edge.id] = edge

            if edge.destination_run_id is not None:
                _edges_by_destination_id[edge.destination_run_id].append(edge)

            if edge.source_run_id is not None:
                _edges_by_source_id[edge.source_run_id].append(edge)

        setattr(
            self, make_cache_name("edges_by_destination_id"), _edges_by_destination_id
        )
        setattr(self, make_cache_name("edges_by_source_id"), _edges_by_source_id)
        setattr(self, make_cache_name("edges_by_id"), _edges_by_id)

    @memoized_property
    def edges_by_destination_id(
        self,
    ) -> Dict[str, List[Edge]]:
        self._populate_edge_mappings()
        return self.edges_by_destination_id

    @memoized_property
    def edges_by_source_id(self) -> Dict[str, List[Edge]]:
        self._populate_edge_mappings()
        return self.edges_by_source_id

    @memoized_property
    def edges_by_id(self) -> Dict[str, Edge]:
        self._populate_edge_mappings()
        return self.edges_by_id

    @memoized_property
    def artifacts_by_id(self) -> Dict[str, Artifact]:
        return {artifact.id: artifact for artifact in self.artifacts}

    def input_artifacts_ready(self, run_id: str) -> bool:
        return all(
            edge.artifact_id is not None
            for edge in self.edges_by_destination_id[run_id]
        )

    def _reverse_execution_order(self, layer_run_ids: List[str]):
        return _sort_layer_runs(
            layer_run_ids, _downstream_edge_filter(self.edges_by_source_id)
        )

    def _execution_order(self, layer_run_ids: List[str]) -> List[str]:
        return _sort_layer_runs(
            layer_run_ids, _upstream_edge_filter(self.edges_by_destination_id)
        )

    def run_ids_sorted_by_layer(
        self, run_sorter: Callable[[List[str]], List[str]]
    ) -> List[str]:
        run_ids: List[str] = []

        def _add_layer_runs(parent_id: Optional[str]):
            layer_run_ids: List[str] = [
                run.id for run in self.runs_by_parent_id[parent_id]
            ]
            ordered_layer_run_ids = run_sorter(layer_run_ids)
            run_ids.extend(ordered_layer_run_ids)

            for run_id in ordered_layer_run_ids:
                _add_layer_runs(run_id)

        _add_layer_runs(None)

        return run_ids

    def get_run_ancestor_ids(self, run_id: str) -> List[str]:
        run = self.runs_by_id[run_id]

        ancestor_ids: List[str] = []

        while run.parent_id is not None:
            ancestor_ids.append(run.parent_id)
            run = self.runs_by_id[run.parent_id]

        return ancestor_ids

    def get_run_descendant_ids(self, run_id: str) -> List[str]:
        descendant_ids: List[str] = []

        child_runs: List[Run] = self.runs_by_parent_id[run_id]

        for child_run in child_runs:
            descendant_ids.append(child_run.id)
            descendant_ids += self.get_run_descendant_ids(child_run.id)

        return descendant_ids

    def get_run_downstream_ids(self, run_id: str) -> List[str]:
        output_edges: List[Edge] = self.edges_by_source_id.get(run_id, [])

        downstream_ids: List[str] = []

        for output_edge in output_edges:
            if output_edge.destination_run_id is not None:
                downstream_ids.append(output_edge.destination_run_id)
                run_id = output_edge.destination_run_id
                output_edge = self.edges_by_source_id.get(run_id)

        return list(set(downstream_ids))

    def clone_futures_by_original_run_id(
        self, storage: Storage, reset_from: Optional[str] = None
    ) -> Tuple[
        OrderedDict[str, AbstractFuture],
        Dict[str, Dict[str, Artifact]],
        Dict[str, Artifact],
    ]:
        value_by_artifact_id: Dict[str, Any] = {}

        futures_by_original_id: Dict[str, AbstractFuture] = {}
        input_artifacts: Dict[str, Dict[str, Artifact]] = defaultdict(dict)
        output_artifacts: Dict[str, Artifact] = {}

        skip_run_ids: List[str] = []
        reset_run_ids: List[str] = []

        if reset_from is not None:
            reset_run_ids.append(reset_from)
            # We will skip descendants of all downstream of reset point
            # plus descendants of downstreams of ancestors
            ancestor_run_ids = self.get_run_ancestor_ids(reset_from)
            reset_run_ids += ancestor_run_ids

            for ancestor_run_id in [reset_from] + ancestor_run_ids:
                downstream_run_ids = self.get_run_downstream_ids(ancestor_run_id)
                reset_run_ids += downstream_run_ids

                for downstream_run_id in downstream_run_ids:
                    downstream_descendant_ids = self.get_run_descendant_ids(
                        downstream_run_id
                    )
                    skip_run_ids += downstream_descendant_ids

        # run order guarantees parents and upstream come first
        run_ids_by_execution_order = self.run_ids_sorted_by_layer(
            run_sorter=self._execution_order
        )

        def _get_artifact_value(artifact: Artifact) -> Any:
            if artifact.id not in value_by_artifact_id:
                value_by_artifact_id[artifact.id] = get_artifact_value(
                    artifact, storage
                )

            return value_by_artifact_id[artifact.id]

        for run_id in run_ids_by_execution_order:

            if run_id in skip_run_ids:
                continue

            run = self.runs_by_id[run_id]

            # Figuring out input kwargs and artifacts
            kwargs: Dict[str, Any] = {}

            input_edges = self.edges_by_destination_id[run.id]

            run_input_artifacts: Dict[str, Artifact] = {}

            for input_edge in input_edges:
                value = None
                if input_edge.artifact_id is not None:
                    artifact = self.artifacts_by_id[input_edge.artifact_id]
                    run_input_artifacts[input_edge.destination_name] = artifact
                    value = _get_artifact_value(artifact)

                if input_edge.source_run_id is not None:
                    kwargs[input_edge.destination_name] = futures_by_original_id[
                        input_edge.source_run_id
                    ]
                elif input_edge.artifact_id is not None:
                    kwargs[input_edge.destination_name] = value
                else:
                    raise RuntimeError("Should not happen")

            func = run.get_func()

            future = func(**kwargs)

            input_artifacts[future.id] = run_input_artifacts

            # Figuring out future output values and artifacts
            output_edges = self.edges_by_source_id[run.id]

            if run_id not in reset_run_ids:
                for output_edge in output_edges:
                    if output_edge.artifact_id is not None:
                        artifact = self.artifacts_by_id[output_edge.artifact_id]
                        output_artifacts[future.id] = artifact
                        value = _get_artifact_value(artifact)
                        future.value = value
                    break

            if run.parent_id is not None:
                parent_future = futures_by_original_id[run.parent_id]
                future.parent_future = parent_future
                for output_edge in output_edges:
                    if output_edge.parent_id is not None:
                        if (
                            self.edges_by_id[output_edge.parent_id].source_run_id
                            == run.parent_id
                        ):
                            parent_future.nested_future = future
                            parent_future.state = FutureState.RAN
                            break

            if FutureState[run.future_state] == FutureState.RESOLVED:  # type: ignore
                if run.id not in reset_run_ids:
                    future.state = FutureState.RESOLVED

            futures_by_original_id[run.id] = future

        if reset_from is None and len(futures_by_original_id) != len(self.runs):
            raise RuntimeError("Not all futures duplicated")

        run_ids_by_reverse_execution_order = self.run_ids_sorted_by_layer(
            run_sorter=self._reverse_execution_order
        )

        return (
            collections.OrderedDict(
                (
                    (run_id, futures_by_original_id[run_id])
                    for run_id in run_ids_by_reverse_execution_order
                    if run_id in futures_by_original_id
                )
            ),
            input_artifacts,
            output_artifacts,
        )


EdgeFilterCallable = Callable[[List[Optional[str]], str], bool]


def _upstream_edge_filter(
    edges_by_destination_id: Dict[str, List[Edge]]
) -> EdgeFilterCallable:
    def _edge_filter(upstream_run_ids: List[Optional[str]], run_id: str):
        return all(
            edge.source_run_id in upstream_run_ids
            for edge in edges_by_destination_id[run_id]
        )

    return _edge_filter


def _downstream_edge_filter(
    edges_by_source_id: Dict[str, List[Edge]]
) -> EdgeFilterCallable:
    def _edge_filter(downstream_run_ids: List[Optional[str]], run_id: str):
        return all(
            edge.destination_run_id in downstream_run_ids
            for edge in edges_by_source_id[run_id]
        )

    return _edge_filter


def _sort_layer_runs(
    layer_run_ids: List[str], edge_filter: EdgeFilterCallable
) -> List[str]:
    def _find_next_runs(previous_run_ids: List[Optional[str]]):
        next_run_ids = [
            run_id
            for run_id in layer_run_ids
            if edge_filter(previous_run_ids, run_id) and run_id not in previous_run_ids
        ]

        if len(next_run_ids) == 0:
            return []

        return next_run_ids + _find_next_runs(
            previous_run_ids + next_run_ids  # type: ignore
        )

    return _find_next_runs([None])
