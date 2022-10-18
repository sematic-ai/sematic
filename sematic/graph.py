# Standard Library
import collections
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, OrderedDict, Tuple

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
        _edges_by_destination_id: Dict[str, Dict[str, Edge]] = defaultdict(dict)

        _edges_by_source_id: Dict[str, List[Edge]] = defaultdict(list)

        _edges_by_id: Dict[str, Edge] = {}

        for edge in self.edges:
            _edges_by_id[edge.id] = edge

            if edge.destination_run_id is not None:
                _edges_by_destination_id[edge.destination_run_id][
                    edge.destination_name
                ] = edge

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
    ) -> Dict[str, Dict[str, Edge]]:
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
            for edge in self.edges_by_destination_id[run_id].values()
        )

    def run_input_edges(self, run_id: str) -> Dict[str, Edge]:
        return self.edges_by_destination_id[run_id]

    @memoized_property
    def runs_sorted_by_layer(self) -> List[Run]:
        runs: List[Run] = []

        def _reverse_execution_order(layer_runs, downstream_run_ids):
            if len(downstream_run_ids) == 0:
                return []
            runs_ = [
                run
                for run in layer_runs
                if all(
                    edge.destination_run_id in downstream_run_ids
                    for edge in self.edges_by_source_id[run.id]
                )
            ]
            return runs_ + _reverse_execution_order(
                layer_runs, [run.id for run in runs_]
            )

        def _add_layer_runs(parent_id: Optional[str]):
            layer_runs: List[Run] = self.runs_by_parent_id[parent_id]
            runs.extend(_reverse_execution_order(layer_runs, [None]))

            # runs.extend(layer_runs)
            for run in layer_runs:
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
    ) -> OrderedDict[str, AbstractFuture]:
        # First we create func/kwargs pairs
        # Some kwargs may be resolved (an artifact exists)
        # Some may be unresolved, we store the source run id to replace
        # later with the corresponding future
        func_kwargs_by_original_id = collections.OrderedDict()

        # Map to find kwargs easily once the source is a future
        unresolved_kwargs_by_source_id: Dict[
            str, List[Tuple[str, str, Dict[str, Any]]]
        ] = collections.defaultdict(list)

        # Map to keep track of what func is not ready to become a future
        # yet
        unresolved_sources_by_run_id: Dict[
            str, Dict[str, str]
        ] = collections.defaultdict(dict)

        value_by_artifact_id: Dict[str, Any] = {}

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

        # """
        # runs order guarantees parents come first
        sorted_runs = self.runs_sorted_by_layer

        for run in sorted_runs:

            if run.id in skip_run_ids:
                continue

            kwargs: Dict[str, Any] = {}

            for name, edge in self.run_input_edges(run.id).items():
                if edge.source_run_id is not None:
                    unresolved_kwargs_by_source_id[edge.source_run_id].append(
                        (run.id, name, kwargs)
                    )
                    unresolved_sources_by_run_id[run.id][name] = edge.source_run_id
                elif edge.artifact_id is not None:
                    value = value_by_artifact_id.get(
                        edge.artifact_id,
                        get_artifact_value(
                            self.artifacts_by_id[edge.artifact_id], storage
                        ),
                    )
                    value_by_artifact_id[edge.artifact_id] = value

                    kwargs[name] = value
                else:
                    raise RuntimeError("Should not happen")

            func = run.get_func()
            func_kwargs_by_original_id[run.id] = (func, kwargs)

        # Now we recreate the future graph

        futures_by_original_id: OrderedDict[str, AbstractFuture] = OrderedDict()

        some_unresolved = True

        while some_unresolved:
            some_unresolved = False
            for original_run_id, (
                func,
                kwargs,
            ) in func_kwargs_by_original_id.items():
                if original_run_id in futures_by_original_id:
                    continue

                if len(unresolved_sources_by_run_id[original_run_id]) != 0:
                    some_unresolved = True
                    continue

                # This func is ready to be converted to a future
                # All inputs are either artifacts or other futures

                future = func(**kwargs)

                # This future is ready to be added to the graph
                # and its func can be removed from the working map
                futures_by_original_id[original_run_id] = future
                # del func_kwargs_by_original_id[original_run_id]

                # We also set this future as kwarg of whoever needs it
                for run_id, name, kwargs in unresolved_kwargs_by_source_id[
                    original_run_id
                ]:
                    kwargs[name] = future
                    del unresolved_sources_by_run_id[run_id][name]

                del unresolved_kwargs_by_source_id[original_run_id]

        # Now we need to figure out the parent future,
        # and whether this future is a nested future
        for original_run_id, future in futures_by_original_id.items():
            parent_id = self.runs_by_id[original_run_id].parent_id

            if parent_id is not None:
                # guaranteed to exist because we sort runs by layers
                parent_future = futures_by_original_id[parent_id]
                future.parent_future = parent_future

                # Is `future` its parent's nested_future?
                output_edges = self.edges_by_source_id[original_run_id]
                for output_edge in output_edges:
                    if output_edge.parent_id is not None:
                        if (
                            self.edges_by_id[output_edge.parent_id].source_run_id
                            == parent_id
                        ):
                            parent_future.nested_future = future
                            break

        if reset_from is None and len(futures_by_original_id) != len(self.runs):
            raise RuntimeError("Not all futures duplicated")

        return collections.OrderedDict(
            ((run.id, futures_by_original_id[run.id]) for run in sorted_runs)
        )

        # return {run.id: futures_by_original_id
