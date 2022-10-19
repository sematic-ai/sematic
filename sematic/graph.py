# Standard Library
import collections
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, OrderedDict, Tuple

# Sematic
from sematic.abstract_future import AbstractFuture
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

    @memoized_property
    def runs_by_id(self) -> Dict[str, Run]:
        return {run.id: run for run in self.runs}

    @memoized_property
    def runs_by_parent_id(self) -> Dict[Optional[str], List[Run]]:
        _runs_by_parent_id: Dict[Optional[str], List[Run]] = defaultdict(list)

        for run in self.runs:
            _runs_by_parent_id[run.parent_id].append(run)

        return _runs_by_parent_id

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
        return getattr(self, make_cache_name("edges_by_destination_id"))

    @memoized_property
    def edges_by_source_id(self) -> Dict[str, List[Edge]]:
        self._populate_edge_mappings()
        return getattr(self, make_cache_name("edges_by_source_id"))

    @memoized_property
    def edges_by_id(self) -> Dict[str, Edge]:
        self._populate_edge_mappings()
        return getattr(self, make_cache_name("edges_id"))

    @memoized_property
    def artifacts_by_id(self) -> Dict[str, Artifact]:
        return {artifact.id: artifact for artifact in self.artifacts}

    def input_artifacts_ready(self, run_id: str) -> bool:
        return all(
            edge.artifact_id is not None
            for edge in self.edges_by_destination_id[run_id]
        )

    def run_input_edges(self, run_id: str) -> Dict[str, Edge]:
        return self.edges_by_destination_id[run_id]

    def _reverse_execution_order(
        self, runs: List[Run], downstream_run_ids: Optional[List[Optional[str]]] = None
    ):
        if downstream_run_ids is None:
            downstream_run_ids = [None]

        upstream_runs = [
            run
            for run in runs
            if all(
                edge.destination_run_id in downstream_run_ids
                for edge in self.edges_by_source_id[run.id]
            )
            and run.id not in downstream_run_ids
        ]

        if len(upstream_runs) == 0:
            return []

        return upstream_runs + self._reverse_execution_order(
            runs, downstream_run_ids + [run.id for run in upstream_runs]
        )

    def _execution_order(
        self, runs: List[Run], upstream_run_ids: Optional[List[Optional[str]]] = None
    ):
        if upstream_run_ids is None:
            upstream_run_ids = [None]

        downstream_runs = [
            run
            for run in runs
            if all(
                edge.source_run_id in upstream_run_ids
                for edge in self.edges_by_destination_id[run.id]
            )
            and run.id not in upstream_run_ids
        ]
        if len(downstream_runs) == 0:
            return []

        return downstream_runs + self._execution_order(
            runs, upstream_run_ids + [run.id for run in downstream_runs]
        )

    def runs_sorted_by_layer(
        self, run_sorter: Callable[[List[Run]], List[Run]]
    ) -> List[Run]:
        runs: List[Run] = []

        def _add_layer_runs(parent_id: Optional[str]):
            layer_runs: List[Run] = self.runs_by_parent_id[parent_id]
            ordered_layer_runs = run_sorter(layer_runs)
            if len(ordered_layer_runs) != len(layer_runs):
                raise RuntimeError("Missing runs in ordered layer runs list")
            runs.extend(ordered_layer_runs)

            for run in ordered_layer_runs:
                _add_layer_runs(run.id)

        _add_layer_runs(None)

        return runs

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

    def get_duplicate_futures_by_original_run_id(
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

        if reset_from is not None:
            # We will skip descendants of all downstream of reset point
            # plus descendants of downstreams of ancestors
            ancestor_run_ids = self.get_run_ancestor_ids(reset_from)
            for ancestor_run_id in [reset_from] + ancestor_run_ids:
                downstream_run_ids = self.get_run_downstream_ids(ancestor_run_id)
                for downstream_run_id in downstream_run_ids:
                    downstream_descendant_ids = self.get_run_descendant_ids(
                        downstream_run_id
                    )
                    skip_run_ids += downstream_descendant_ids

        # runs order guarantees parents come first
        run_by_execution_order = self.runs_sorted_by_layer(self._execution_order)

        def _get_edge_artifact(edge: Edge):
            if edge.artifact_id is None:
                return None

            return value_by_artifact_id.get(
                edge.artifact_id,
                get_artifact_value(self.artifacts_by_id[edge.artifact_id], storage),
            )

        for run in run_by_execution_order:

            if run.id in skip_run_ids:
                continue

            kwargs: Dict[str, Any] = {}
            func = run.get_func()

            input_edges = self.edges_by_destination_id[run.id]
            output_edges = self.edges_by_source_id[run.id]

            run_input_artifacts: Dict[str, Artifact] = {}

            for edge in input_edges:
                value = None
                if edge.artifact_id is not None:
                    artifact = self.artifacts_by_id[edge.artifact_id]
                    run_input_artifacts[edge.destination_name] = artifact
                    if edge.artifact_id not in value_by_artifact_id:
                        value_by_artifact_id[edge.artifact_id] = get_artifact_value(
                            artifact, storage
                        )
                    value = value_by_artifact_id[edge.artifact_id]

                if edge.source_run_id is not None:
                    kwargs[edge.destination_name] = futures_by_original_id[
                        edge.source_run_id
                    ]
                elif edge.artifact_id is not None:
                    kwargs[edge.destination_name] = value
                else:
                    raise RuntimeError("Should not happen")

            future = func(**kwargs)

            input_artifacts[future.id] = run_input_artifacts

            for output_edge in output_edges:
                if output_edge.artifact_id is not None:
                    artifact = self.artifacts_by_id[output_edge.artifact_id]
                    output_artifacts[future.id] = artifact
                    value = _get_edge_artifact(output_edge)
                    future.value = value
                    value_by_artifact_id[output_edge.artifact_id] = value
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
                            break

            futures_by_original_id[run.id] = future

        if reset_from is None and len(futures_by_original_id) != len(self.runs):
            raise RuntimeError("Not all futures duplicated")

        run_by_reverse_execution_order = self.runs_sorted_by_layer(
            self._reverse_execution_order
        )

        return (
            collections.OrderedDict(
                (
                    (run.id, futures_by_original_id[run.id])
                    for run in run_by_reverse_execution_order
                    if run.id in futures_by_original_id
                )
            ),
            input_artifacts,
            output_artifacts,
        )
