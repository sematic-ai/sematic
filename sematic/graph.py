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
from sematic.utils.memoized_property import (
    make_cache_name,
    memoized_indexed,
    memoized_property,
)


@dataclass
class Graph:

    runs: List[Run]
    edges: List[Edge]
    artifacts: List[Artifact]

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
        """
        Does run have all input artifacts ready, i.e. upstream runs have
        resolved?
        """
        return all(
            edge.artifact_id is not None
            for edge in self.edges_by_destination_id[run_id]
        )

    def _execution_order(self, layer_run_ids: List[str]) -> List[str]:
        """
        For a given graph layer (all runs have the same parent_id), this will
        return run_ids in order of execution, i.e. upstream runs first,
        downstream runs next. This is not deterministic, as multiple runs may
        have the same set of upstream runs, and thus can be executed in
        parallel.

        Parameters
        ----------
        layer_run_ids: List[str]
            IDs of runs in the layer. All runs are epxected to have the same
            parent_id.
        """
        return _sort_layer_runs(
            layer_run_ids, _upstream_edge_filter(self.edges_by_destination_id)
        )

    def _reverse_execution_order(self, layer_run_ids: List[str]):
        """
        For a given graph layer (all runs have the same parent_id), this will
        return run_ids in order of reverse execution, i.e. downstream first,
        upstream runs next. This is not deterministic, as runs may have multiple
        upstream runs.

        Parameters
        ----------
        layer_run_ids: List[str]
            IDs of runs in the layer. All runs are epxected to have the same
            parent_id.
        """
        return _sort_layer_runs(
            layer_run_ids, _downstream_edge_filter(self.edges_by_source_id)
        )

    def _run_ids_sorted_by_layer(
        self, run_sorter: Callable[[List[str]], List[str]]
    ) -> List[str]:
        """
        Run IDs grouped by parent_ids, with parent_ids sorted from outermost
        (None) to innermost. This is not deterministic as multiple layers may
        have the same parent_id.

        Within a layer, runs are sorted with the run_sorter input callable.

        Parameters
        ----------
        run_sorter: Callable[[List[str]], List[str]]
            Callable to sort run_ids within a layer

        Returns
        -------
        List[str]
            A flat list of run IDs.
        """
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

    @memoized_indexed
    def _get_run_ancestor_ids(self, run_id: str) -> List[str]:
        """
        Get a run's ancestor IDs, sorter by increasing proximity, i.e. direct
        parent first, and going up.

        Parameters
        ----------
        run_id: str
            ID of child run

        Returns
        -------
        List[str]
            List of ancestor run IDs
        """
        run = self.runs_by_id[run_id]

        ancestor_ids: List[str] = []

        while run.parent_id is not None:
            ancestor_ids.append(run.parent_id)
            run = self.runs_by_id[run.parent_id]

        return ancestor_ids

    @memoized_indexed
    def _get_run_descendant_ids(self, run_id: str) -> List[str]:
        """
        Get a run's descendant IDs, depth-first.
        """
        descendant_ids: List[str] = []

        child_runs: List[Run] = self.runs_by_parent_id[run_id]

        for child_run in child_runs:
            descendant_ids.append(child_run.id)
            descendant_ids += self._get_run_descendant_ids(child_run.id)

        return descendant_ids

    @memoized_indexed
    def _get_run_downstream_ids(self, run_id: str) -> List[str]:
        """
        Within a given layer, get a run's downstream run IDs, depth-first.
        """
        output_edges: List[Edge] = self.edges_by_source_id.get(run_id, [])

        downstream_ids: List[str] = []

        for output_edge in output_edges:
            if output_edge.destination_run_id is not None:
                downstream_ids.append(output_edge.destination_run_id)
                downstream_ids += self._get_run_downstream_ids(
                    output_edge.destination_run_id
                )

        return list(set(downstream_ids))

    def clone_futures(
        self, storage: Storage, reset_from: Optional[str] = None
    ) -> Tuple[
        OrderedDict[str, AbstractFuture],
        Dict[str, Dict[str, Artifact]],
        Dict[str, Artifact],
    ]:
        """
        Clones the current graph into new futures.

        Future state is set as follows:

        - If run is RAN or RESOLVED, future state is set accordingly. If
          reset_from, see behavior below.

        - If run is FAILED, NESTED_FAILED, or CANCELED, future state is set to
          CREATED

        If reset_from is not None, all ancestor runs are set to RAN or CREATED
        depending on original run status. Cloned futures of all downstream runs
        of reset_from are set to CREATED. All descendant runs of all downstream
        runs of all ancestors are set to CREATED.

        If reset_from is None, only FAILED, NESTED_FAILED, and CANCELED runs
        will be reset.

        Parameters
        ----------
        storage: Storage
            The storage class to retrieve artifact values and set future.value
            and future.kwargs appropriately.

        reset_from: Optional[str]
            Force reset other runs than only failed ones.

        Returns
        -------
        Tuple[List[AbstractFuture], Dict[str, Dict[str, Artifact]], Dict[str,
        Artifact]]
            A tuple whose first element is a list of cloned futures, grouped by
            nested layers (outermost first), and sorted by reverse execution
            order within each layer. The second element is

        """
        value_by_artifact_id: Dict[str, Any] = {}

        futures_by_original_id: Dict[str, AbstractFuture] = {}
        input_artifacts: Dict[str, Dict[str, Artifact]] = defaultdict(dict)
        output_artifacts: Dict[str, Artifact] = {}

        # We skip descendants of all downstream of reset point
        # plus descendants of downstreams of ancestors
        # The skipped futures will be naturally re-created by the new graph
        # resolution
        skip_run_ids: List[str] = []

        # reset = forcing future state to CREATED or RAN
        # Considering reset_from and ancestors runs, we reset the run and
        # all downstream
        reset_run_ids: List[str] = []

        if reset_from is not None:
            reset_run_ids.append(reset_from)
            ancestor_run_ids = self._get_run_ancestor_ids(reset_from)
            reset_run_ids += ancestor_run_ids

            for ancestor_run_id in [reset_from] + ancestor_run_ids:
                downstream_run_ids = self._get_run_downstream_ids(ancestor_run_id)
                reset_run_ids += downstream_run_ids

                for downstream_run_id in downstream_run_ids:
                    downstream_descendant_ids = self._get_run_descendant_ids(
                        downstream_run_id
                    )
                    skip_run_ids += downstream_descendant_ids

        # run order guarantees parents and upstream come first
        # This is necessary because we want upstream cloned futures
        # to be created before downstreams so that the appropriate
        # kwargs can be built
        run_ids_by_execution_order = self._run_ids_sorted_by_layer(
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

            # Figuring out parent and nested futures
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

                            if run.id in reset_run_ids:
                                parent_future.state = FutureState.RAN

                            break

            # Settings state for resolved runs unless reset
            if FutureState[run.future_state] == FutureState.RESOLVED:  # type: ignore
                if run.id not in reset_run_ids:
                    future.state = FutureState.RESOLVED

            futures_by_original_id[run.id] = future

        if reset_from is None and len(futures_by_original_id) != len(self.runs):
            raise RuntimeError("Not all futures duplicated")

        # We return future sorted by how they would be sorted for a resolution
        # from scratch: grouped by layer (outermost first), and sorter in reverse
        # execution order within each layer
        run_ids_by_reverse_execution_order = self._run_ids_sorted_by_layer(
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
