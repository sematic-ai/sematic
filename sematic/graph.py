# Standard Library
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from enum import Enum, unique
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple
from typing import OrderedDict as OrderedDictType

# Sematic
import sematic.api_client as api_client
from sematic.abstract_future import AbstractFuture, FutureState
from sematic.db.models.artifact import Artifact
from sematic.db.models.edge import Edge
from sematic.db.models.factories import initialize_future_from_run
from sematic.db.models.run import Run
from sematic.utils.algorithms import breadth_first_search, topological_sort
from sematic.utils.memoized_property import memoized_indexed, memoized_property


RunID = str
RunsByID = Dict[RunID, Run]
RunsByParentID = Dict[Optional[RunID], List[Run]]
EdgesByRunID = Dict[RunID, List[Edge]]
EdgesByID = Dict[str, Edge]


@unique
class RerunMode(Enum):
    """How to choose which parts of the graph need to be rerun.

    Attributes
    ----------
    SPECIFIC_RUN:
        Invalidate a specific run and all its descendants. Then execute
        whatever runs are required to determine the final result of the
        graph.
    CONTINUE:
        Clone the state of the provided pipeline run, then
        execute only runs that are required to determine the final
        result of the graph.
    REENTER:
        Attempt to recreate an existing future graph in memory
        and pick up where it was left off. This differs from
        CONTINUE in that CONTINUE represents an entirely new
        graph (cloned from an original), while REENTER uses
        the existing graph.
    """

    SPECIFIC_RUN = "SPECIFIC_RUN"
    CONTINUE = "CONTINUE"

    # We keep CONTINUE as distinct because it can still be used to rerun from failed.
    REENTER = "REENTER"


@dataclass
class FutureGraph:
    """A graph of futures and their associated artifacts.

    Attributes
    ----------
    futures_by_run_id:
        A dictionary of futures stored using the id of a corresponding run.
        This can be the id of the future itself, or potentially a run that
        the future was derived from.
    input_artifacts:
        A dictionary mapping a run id to the input artifacts for that run.
        The input artifacts for a given run will itself be a dictionary from
        the name of the input parameter for the run to the Artifact object
        that should be used as its input. The graph may be in a partially
        executed state, in which case not all runs may have known input
        artifacts.
    output_artifacts:
        A dictionary mapping run ids to the Artifact object resulting from
        that run. The graph may be in a partially executed state, in which
        case not all runs will have known output artifacts.
    """

    futures_by_run_id: OrderedDictType[RunID, AbstractFuture] = field(
        init=False, default_factory=OrderedDict
    )
    input_artifacts: Dict[RunID, Dict[str, Artifact]] = field(
        init=False, default_factory=lambda: defaultdict(dict)
    )
    output_artifacts: Dict[RunID, Artifact] = field(init=False, default_factory=dict)

    def sort_by(self, run_ids: List[RunID]):
        """Sort futures in-place according to the order of run_ids."""
        ordered_futures = OrderedDict(
            (
                (run_id, self.futures_by_run_id[run_id])
                for run_id in run_ids
                if run_id in self.futures_by_run_id
            )
        )
        self.futures_by_run_id = ordered_futures


@dataclass
class ClonedFutureGraph(FutureGraph):
    """
    A cloned future graph. This graph is potentially partial, as it is meant to
    be used as a resolution seed.

    Its futures_by_run_id field maps the id of a run to the future cloned from that
    run.
    """

    def set_root_future_id(self, root_id: str):
        """Update the id of the root future in this graph to match the passed one."""
        root_future = next(
            future
            for future in self.futures_by_run_id.values()
            if future.is_root_future()
        )

        if root_future.id in self.input_artifacts:
            self.input_artifacts[root_id] = self.input_artifacts[root_future.id]
            del self.input_artifacts[root_future.id]

        if root_future.id in self.output_artifacts:
            self.output_artifacts[root_id] = self.output_artifacts[root_future.id]
            del self.output_artifacts[root_future.id]

        root_future.id = root_id


@dataclass
class Graph:
    """
    Represents an existing immutable graph.

    Nomenclature
    ------------
    Parent run
        The run corresponding to the function calling the current run's function
    Child run
        The run corresponding to the function being called by the current run's
        function
    Layer
        Sibling runs. All runs with same parent.
    Ancestor runs
        All parents going up to the root
    Descendant runs
        All children down to the leaves
    Upstream runs
        Within a given layer, runs corresponding to functions being called prior
        to the current run's function. Current function depends on outputs of
        upstream runs.
    Downstream runs
        Within a given layer, runs corresponding to functions being called after
        the current run's function. Downstream runs depend on outputs of current
        function.

    Parameters
    ----------
    runs: List[Run]
        The runs in the graph. Unordered.
    edges: List[Edge]
        Edges between runs. Unordered.
    artifacts: List[Artifact]
        Artifacts attached to edges. Unordered.
    """

    # Using Iterable to satisfy mypy when passing a list to __init__
    # but post_init forces tuples for safety
    runs: Iterable[Run]
    edges: Iterable[Edge]
    artifacts: Iterable[Artifact]

    def __post_init__(self):
        self.runs = tuple(self.runs)
        self.edges = tuple(self.edges)
        self.artifacts = tuple(self.artifacts)

    @memoized_property
    def _run_mappings(self) -> Tuple[RunsByID, RunsByParentID]:
        _runs_by_id: RunsByID = dict()
        _runs_by_parent_ids: RunsByParentID = defaultdict(list)

        for run in self.runs:
            _runs_by_id[run.id] = run
            _runs_by_parent_ids[run.parent_id].append(run)

        return _runs_by_id, _runs_by_parent_ids

    @property
    def _runs_by_id(self) -> RunsByID:
        return self._run_mappings[0]

    @property
    def _runs_by_parent_id(self) -> RunsByParentID:
        return self._run_mappings[1]

    @memoized_property
    def _edge_mappings(self) -> Tuple[EdgesByID, EdgesByRunID, EdgesByRunID]:
        _edges_by_destination_id: EdgesByRunID = defaultdict(list)

        _edges_by_source_id: EdgesByRunID = defaultdict(list)

        _edges_by_id: EdgesByID = {}

        for edge in self.edges:
            _edges_by_id[edge.id] = edge

            if edge.destination_run_id is not None:
                _edges_by_destination_id[edge.destination_run_id].append(edge)

            if edge.source_run_id is not None:
                _edges_by_source_id[edge.source_run_id].append(edge)

        return _edges_by_id, _edges_by_source_id, _edges_by_destination_id

    @property
    def _edges_by_destination_id(self) -> EdgesByRunID:
        return self._edge_mappings[2]

    @property
    def _edges_by_source_id(self) -> EdgesByRunID:
        return self._edge_mappings[1]

    @property
    def _edges_by_id(self) -> EdgesByID:
        return self._edge_mappings[0]

    @memoized_property
    def _artifacts_by_id(self) -> Dict[str, Artifact]:
        return {artifact.id: artifact for artifact in self.artifacts}

    def input_artifacts_ready(self, run_id: RunID) -> bool:
        """
        Does run have all input artifacts ready, i.e. upstream runs have
        resolved? Uses in-memory graph artifacts, does not fetch them from the DB.
        """
        return all(
            edge.artifact_id is not None for edge in self._edges_by_destination_id[run_id]
        )

    def _execution_order(self, layer_run_ids: List[RunID]) -> List[RunID]:
        """
        For a given graph layer (all runs have the same parent_id), this will
        return run_ids in order of execution, i.e. upstream runs first,
        downstream runs next. Parallelizable run IDs are sorted alphabetically for
        determinism. Returns a flat list, thus is not suitable to determine
        whether one run is a dependency of another.

        Parameters
        ----------
        layer_run_ids: List[str]
            IDs of runs in the layer. All runs are epxected to have the same
            parent_id.
        """
        if len({self._runs_by_id[run_id].parent_id for run_id in layer_run_ids}) > 1:
            raise ValueError("Runs are not all from the same layer")

        dependencies = {
            run_id: [edge.source_run_id for edge in self._edges_by_destination_id[run_id]]
            for run_id in layer_run_ids
        }
        return topological_sort(dependencies)

    def _reverse_execution_order(self, layer_run_ids: List[RunID]) -> List[RunID]:
        """
        For a given graph layer (all runs have the same parent_id), this will
        return run_ids in order of reverse execution, i.e. downstream first,
        upstream runs next. Parallelizable run IDs are sorted alphabetically for
        determinism. Returns a flat list, thus is not suitable to determine
        whether one run is a dependency of another.

        Parameters
        ----------
        layer_run_ids: List[str]
            IDs of runs in the layer. All runs are epxected to have the same
            parent_id.
        """
        if len({self._runs_by_id[run_id].parent_id for run_id in layer_run_ids}) > 1:
            raise ValueError("Runs are not all from the same layer")

        dependencies = {
            run_id: [edge.destination_run_id for edge in self._edges_by_source_id[run_id]]
            for run_id in layer_run_ids
        }
        return topological_sort(dependencies)

    def _sorted_run_ids_by_layer(
        self, run_sorter: Callable[[List[RunID]], List[RunID]]
    ) -> List[RunID]:
        """
        Run IDs grouped by parent_ids, with parent_ids sorted from outermost
        (None) to innermost. Breadth-first sorting.

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
        layers = {
            parent_id: [run.id for run in runs]
            for parent_id, runs in self._runs_by_parent_id.items()
        }

        run_ids = []

        start_nodes = [r.id for r in self._runs_by_parent_id[None]]

        def get_next(run_id):
            sorted = run_sorter(layers.get(run_id, []))
            return sorted

        def visit(run_id):
            run_ids.append(run_id)

        breadth_first_search(
            start=start_nodes,
            get_next=get_next,
            visit=visit,
        )

        return run_ids

    @memoized_indexed
    def _get_run_ancestor_ids(self, run_id: RunID) -> List[RunID]:
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
        run = self._runs_by_id[run_id]

        ancestor_ids: List[RunID] = []

        while run.parent_id is not None:
            ancestor_ids.append(run.parent_id)
            run = self._runs_by_id[run.parent_id]

        return ancestor_ids

    @memoized_indexed
    def _get_run_descendant_ids(self, run_id: RunID) -> List[RunID]:
        """
        Get a run's descendant IDs, depth-first.
        """
        descendant_ids: List[RunID] = []

        child_runs: List[Run] = self._runs_by_parent_id[run_id]

        for child_run in child_runs:
            descendant_ids.append(child_run.id)
            descendant_ids += self._get_run_descendant_ids(child_run.id)

        return descendant_ids

    @memoized_indexed
    def _get_run_downstream_ids(self, run_id: RunID) -> List[RunID]:
        """
        Within a given layer, get a run's downstream run IDs, depth-first.
        """
        output_edges: List[Edge] = self._edges_by_source_id.get(run_id, [])

        downstream_ids: List[RunID] = []

        for output_edge in output_edges:
            if output_edge.destination_run_id is not None:
                downstream_ids.append(output_edge.destination_run_id)
                downstream_ids += self._get_run_downstream_ids(
                    output_edge.destination_run_id
                )

        return list(set(downstream_ids))

    def _get_skip_reset_run_ids(
        self, reset_from: Optional[RunID]
    ) -> Tuple[List[RunID], List[RunID]]:
        """
        Figures out what run IDs to skip or reset based on rerun_from.

        If reset_from is a run id, we skip descendants of reset point
        and descendants of downstreams of reset point and ancestors.
        The skipped futures will be naturally re-created by the new
        graph resolution.

        If reset_from is None, we skip nothing and reset anything that
        was not in one of RAN, RESOLVED, or NESTED_FAILED.

        reset = forcing future state to CREATED or RAN. Considering reset_from
        and ancestors runs, we reset the run and all downstream.

        Parameters
        ----------
        reset_from: RunID
            ID of run from which to reset the graph

        Returns
        -------
        Tuple[List[RunID], List[RunID]]
            A tuple whose first element is the list of run IDs to skip when
            cloning the graph. The second element is the list of run IDs whose
            cloned future's state to reset to CREATED.
        """
        skip_run_ids: List[RunID] = []
        reset_run_ids = []

        if reset_from is None:
            run_ids_by_execution_order = self._sorted_run_ids_by_layer(
                run_sorter=self._execution_order
            )
            if len(run_ids_by_execution_order) == 0:
                return [], []

            doesnt_require_rerun_states = {
                FutureState.RESOLVED.value,
                FutureState.RAN.value,
                # If the run is "nested" failed, then the run itself
                # executed fine, it just has a child/descendant that needs
                # to be re-executed.
                FutureState.NESTED_FAILED.value,
            }
            runs_by_id = self._runs_by_id
            reset_run_ids = [
                run_id
                for run_id in run_ids_by_execution_order
                if runs_by_id[run_id].future_state not in doesnt_require_rerun_states
            ]

            return skip_run_ids, reset_run_ids

        skip_run_ids = self._get_run_descendant_ids(reset_from)

        reset_run_ids = [reset_from]

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

        return skip_run_ids, reset_run_ids

    @memoized_indexed
    def _get_artifact_value(self, artifact_id: str) -> Any:
        artifact = self._artifacts_by_id[artifact_id]
        return api_client.get_artifact_value(artifact)

    def _get_future_inputs(
        self, run_id: RunID, future_graph: FutureGraph
    ) -> Tuple[Dict[str, Any], Dict[str, Artifact]]:
        kwargs: Dict[str, Any] = {}

        input_edges = self._edges_by_destination_id[run_id]

        run_input_artifacts: Dict[str, Artifact] = {}

        for input_edge in input_edges:
            if input_edge.destination_name is None:
                raise RuntimeError("Input edge misses destination name")

            value = None

            if input_edge.artifact_id is not None:
                artifact = self._artifacts_by_id[input_edge.artifact_id]
                run_input_artifacts[input_edge.destination_name] = artifact
                value = self._get_artifact_value(artifact.id)

            if input_edge.source_run_id is not None:
                # We set the input as the upstream future to mimic what
                # happens in a greenfield resolution.
                kwargs[input_edge.destination_name] = future_graph.futures_by_run_id[
                    input_edge.source_run_id
                ]

            elif input_edge.artifact_id is not None:
                kwargs[input_edge.destination_name] = value
            else:
                raise RuntimeError(
                    "Invalid input edge had no source run or associated artifact"
                )

        return kwargs, run_input_artifacts

    def _get_run_output(self, run_id: RunID) -> Tuple[Any, Optional[Artifact]]:
        output_edges = self._edges_by_source_id[run_id]

        for output_edge in output_edges:
            if output_edge.artifact_id is None:
                return None, None

            artifact = self._artifacts_by_id[output_edge.artifact_id]
            value = self._get_artifact_value(artifact.id)
            return value, artifact

        return None, None

    def _set_parent_future_using_run(
        self,
        future: AbstractFuture,
        run: Run,
        future_graph: FutureGraph,
    ) -> None:
        """Use this run graph and provided run to set the parent future in future_graph.

        To be used in the process of constructing a FutureGraph from this run graph
        (potentially as a cloned future graph). This method will update futures in
        future_graph in-place.

        The parent run of the provided run will be used to identify the appropriate
        parent future for the provided future. The provided future and its parent
        future will be modified as necessary.

        Parameters
        ----------
        future:
           The future whose parent should be updated.
        run:
            The run to be used as a reference to update the future's parent.
        future_graph:
            The future graph being constructed.
        """
        if run.parent_id is None:
            return

        parent_future = future_graph.futures_by_run_id[run.parent_id]

        future.parent_future = parent_future

        # Is future parent_future's nested future?
        if self._runs_by_id[run.parent_id].nested_future_id == run.id:
            parent_future.nested_future = future

    def _clone_future(
        self, run_id: RunID, cloned_graph: ClonedFutureGraph, reset_run_ids: List[RunID]
    ) -> AbstractFuture:
        run = self._runs_by_id[run_id]

        kwargs, run_input_artifacts = self._get_future_inputs(run_id, cloned_graph)

        future = initialize_future_from_run(run, kwargs, use_same_id=False)

        # For cloning a graph, we want the default state of the future to be
        # created unless explicitly updated to a different value.
        future.props.state = FutureState.CREATED

        cloned_graph.input_artifacts[future.id] = run_input_artifacts

        if run_id not in reset_run_ids:
            value, output_artifact = self._get_run_output(run_id)
            if output_artifact is not None:
                cloned_graph.output_artifacts[future.id] = output_artifact
                future.value = value

        self._set_parent_future_using_run(future, run, cloned_graph)

        # Is future parent_future's nested future?
        if (
            run.parent_id is not None
            and self._runs_by_id[run.parent_id].nested_future_id == run.id
        ):
            parent_future = cloned_graph.futures_by_run_id[run.parent_id]
            if run.id in reset_run_ids:
                parent_future.state = FutureState.RAN

        # Settings state for resolved runs unless reset
        if FutureState[run.future_state] == FutureState.RESOLVED:  # type: ignore
            if run_id not in reset_run_ids:
                future.state = FutureState.RESOLVED
                # if the original run was cloned as well, get the first ever run id
                future.original_future_id = (
                    run.original_run_id if run.original_run_id is not None else run_id
                )

        return future

    def _future_from_run(
        self, run_id: RunID, future_graph: FutureGraph
    ) -> AbstractFuture:
        run = self._runs_by_id[run_id]
        kwargs, run_input_artifacts = self._get_future_inputs(run_id, future_graph)

        future = initialize_future_from_run(run, kwargs)
        future_graph.input_artifacts[future.id] = run_input_artifacts

        value, output_artifact = self._get_run_output(run_id)
        if output_artifact is not None:
            future_graph.output_artifacts[future.id] = output_artifact
            future.value = value

        self._set_parent_future_using_run(future, run, future_graph)

        return future

    def clone_futures(self, reset_from: Optional[RunID] = None) -> ClonedFutureGraph:
        """
        Clones the current graph into new futures.

        Future state is set as follows:

        - If run is RAN or RESOLVED, future state is set accordingly. If
          reset_from is not None, see behavior below.

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
            Force reset descendant/downstream runs if this is not None. If it is None,
            will use the CONTINUE `RerunMode`.

        Returns
        -------
        ClonedFutureGraph
            A dataclass containing an ordered mapping of original run ids to cloned
            futures, grouped by nested layers (outermost first), and sorted by reverse
            execution order within each layer. The second field is a mapping of future
            IDs to input artifacts. The third element is a mapping of future IDs
            to output artifacts.
        """
        cloned_graph = ClonedFutureGraph()

        skip_run_ids, reset_run_ids = self._get_skip_reset_run_ids(reset_from)

        # run order guarantees parents and upstream come first
        # This is necessary because we want upstream cloned futures
        # to be created before downstreams so that the appropriate
        # kwargs can be built
        run_ids_by_execution_order = self._sorted_run_ids_by_layer(
            run_sorter=self._execution_order
        )

        for run_id in run_ids_by_execution_order:
            if run_id in skip_run_ids:
                continue

            cloned_graph.futures_by_run_id[run_id] = self._clone_future(
                run_id, cloned_graph, reset_run_ids
            )

        if reset_from is None and len(cloned_graph.futures_by_run_id) != len(
            list(self.runs)
        ):
            raise RuntimeError("Not all futures duplicated")

        # We return future sorted by how they would be sorted for a resolution
        # from scratch: grouped by layer (outermost first), and sorter in reverse
        # execution order within each layer
        run_ids_by_reverse_execution_order = self._sorted_run_ids_by_layer(
            run_sorter=self._reverse_execution_order
        )

        cloned_graph.sort_by(run_ids_by_reverse_execution_order)

        return cloned_graph

    def to_future_graph(self) -> FutureGraph:
        """Convert this `Run` graph into a corresponding graph of `Future`s.

        The future graph will use all the same ids as the runs.
        """
        future_graph = FutureGraph()

        # run order guarantees parents and upstream come first
        # This is necessary because we want upstream futures
        # to be created before downstreams so that the appropriate
        # kwargs can be built
        run_ids_by_execution_order = self._sorted_run_ids_by_layer(
            run_sorter=self._execution_order
        )

        for run_id in run_ids_by_execution_order:
            future_graph.futures_by_run_id[run_id] = self._future_from_run(
                run_id, future_graph
            )

        if len(future_graph.futures_by_run_id) != len(list(self.runs)):
            raise RuntimeError("Not all futures duplicated")

        # We return future sorted by how they would be sorted for a resolution
        # from scratch: grouped by layer (outermost first), and sorter in reverse
        # execution order within each layer
        run_ids_by_reverse_execution_order = self._sorted_run_ids_by_layer(
            run_sorter=self._reverse_execution_order
        )

        future_graph.sort_by(run_ids_by_reverse_execution_order)

        return future_graph
