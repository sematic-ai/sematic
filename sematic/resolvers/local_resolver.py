# Standard Library
import datetime
import logging
import uuid
from typing import Dict, List, Optional, Tuple, Union

# Sematic
import sematic.api_client as api_client
from sematic.abstract_calculator import CalculatorError
from sematic.abstract_future import AbstractFuture, FutureState
from sematic.config import get_config  # noqa: F401
from sematic.db.models.artifact import Artifact
from sematic.db.models.edge import Edge
from sematic.db.models.factories import make_artifact, make_run_from_future
from sematic.db.models.resolution import Resolution, ResolutionKind, ResolutionStatus
from sematic.db.models.run import Run
from sematic.resolvers.silent_resolver import SilentResolver
from sematic.user_settings import get_all_user_settings
from sematic.utils.exceptions import format_exception_for_run

logger = logging.getLogger(__name__)


class LocalResolver(SilentResolver):
    """
    A resolver to resolver a graph in-memory.

    Each Future's resolution is tracked in the DB as a run. Each individual function's
    input argument and output value is tracked as an artifact.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._edges: Dict[str, Edge] = {}
        self._runs: Dict[str, Run] = {}
        self._artifacts: Dict[str, Artifact] = {}

        # Buffers for persistency
        self._buffer_edges: Dict[str, Edge] = {}
        self._buffer_runs: Dict[str, Run] = {}
        self._buffer_artifacts: Dict[str, Artifact] = {}

        # TODO: Replace this with a local storage engine
        self._store_artifacts = False

    def _update_edge(
        self,
        source_run_id: Optional[str],
        destination_run_id: Optional[str],
        destination_name: Optional[str],
        artifact_id: Optional[str],
        parent_id: Optional[str],
    ):
        """
        Creates or updates an edge in the graph.
        """
        edge = Edge(
            id=uuid.uuid4().hex,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
            source_run_id=source_run_id,
            destination_run_id=destination_run_id,
            destination_name=destination_name,
            artifact_id=artifact_id,
            parent_id=parent_id,
        )

        edge_key = make_edge_key(edge)

        edge = self._edges.get(edge_key, edge)
        if edge.artifact_id is None and artifact_id is not None:
            edge.artifact_id = artifact_id

        self._add_edge(edge)

    def _get_input_edge(self, destination_run_id, destination_name) -> Optional[Edge]:
        """
        Find an input edge.
        """
        for edge in self._edges.values():
            if (
                edge.destination_run_id == destination_run_id
                and edge.destination_name == destination_name
            ):
                return edge

        return None

    def _get_output_edges(self, source_run_id: str) -> List[Edge]:
        """
        Find output edges.
        There can be multiple ones if the output goes to multiple futures.
        """
        return [
            edge for edge in self._edges.values() if edge.source_run_id == source_run_id
        ]

    def _populate_run_and_artifacts(self, future: AbstractFuture) -> Run:
        if len(future.kwargs) != len(future.resolved_kwargs):
            raise RuntimeError("Not all input arguments are resolved")

        input_artifacts = {}
        for name, value in future.resolved_kwargs.items():
            artifact = make_artifact(
                value, future.calculator.input_types[name], store=self._store_artifacts
            )
            self._add_artifact(artifact)
            input_artifacts[name] = artifact

        run = self._populate_graph(future, input_artifacts=input_artifacts)

        return run

    def _resolution_will_start(self):
        self._populate_run_and_artifacts(self._root_future)
        self._save_graph()
        self._create_resolution(self._root_future.id, detached=False)
        self._update_resolution_status(ResolutionStatus.RUNNING)

    def _get_resolution_image(self) -> Optional[str]:
        return None

    def _get_resolution_kind(self, detached) -> ResolutionKind:
        return ResolutionKind.LOCAL

    def _create_resolution(self, root_future_id, detached):
        resolution = Resolution(
            root_id=root_future_id,
            status=ResolutionStatus.SCHEDULED,
            kind=self._get_resolution_kind(detached),
            docker_image_uri=self._get_resolution_image(),
            settings_env_vars={
                name: str(value) for name, value in get_all_user_settings().items()
            },
        )
        api_client.save_resolution(resolution)

    def _future_will_schedule(self, future: AbstractFuture) -> None:
        super()._future_will_schedule(future)

        run = self._populate_run_and_artifacts(future)

        run.future_state = FutureState.SCHEDULED
        run.root_id = self._futures[0].id
        run.started_at = datetime.datetime.utcnow()

        self._add_run(run)
        self._save_graph()

    def _future_did_schedule(self, future: AbstractFuture) -> None:
        super()._future_did_schedule(future)
        root_future = self._futures[0]
        if root_future.id == future.id:
            api_client.notify_pipeline_update(self._runs[future.id].calculator_path)

    def _future_did_run(self, future: AbstractFuture) -> None:
        super()._future_did_run(future)

        run = self._get_run(future.id)

        if future.parent_future is not None:
            run.parent_id = future.parent_future.id

        run.future_state = FutureState.RAN
        run.ended_at = datetime.datetime.utcnow()

        if future.nested_future is None:
            raise Exception("Missing nested future")

        self._populate_graph(future.nested_future)
        self._add_run(run)
        self._save_graph()

    def _get_output_artifact(self, run_id: str) -> Optional[Artifact]:
        return None

    def _future_did_resolve(self, future: AbstractFuture) -> None:
        super()._future_did_resolve(future)

        run = self._get_run(future.id)
        run.future_state = FutureState.RESOLVED
        run.resolved_at = datetime.datetime.utcnow()

        output_artifact = self._get_output_artifact(future.id)
        if output_artifact is None:
            output_artifact = make_artifact(future.value, future.calculator.output_type)
            self._add_artifact(output_artifact)

        self._populate_graph(future, output_artifact=output_artifact)
        self._add_run(run)
        self._save_graph()

    def _future_did_fail(self, failed_future: AbstractFuture) -> None:
        super()._future_did_fail(failed_future)

        run = self._get_run(failed_future.id)

        run.future_state = failed_future.state

        # We do not propagate exceptions to parent runs
        if failed_future.state == FutureState.FAILED:
            run.exception = format_exception_for_run()

        run.failed_at = datetime.datetime.utcnow()
        self._add_run(run)
        self._save_graph()

    def _notify_pipeline_update(self):
        root_future = self._futures[0]
        api_client.notify_pipeline_update(self._runs[root_future.id].calculator_path)

    def _resolution_did_succeed(self) -> None:
        super()._resolution_did_succeed()
        self._update_resolution_status(ResolutionStatus.COMPLETE)
        self._notify_pipeline_update()

    def _resolution_did_fail(self, error: Exception) -> None:
        super()._resolution_did_fail(error)
        if isinstance(error, CalculatorError):
            reason = "Marked as failed because another run in the graph failed."
            resolution_status = ResolutionStatus.COMPLETE
        else:
            reason = (
                "Marked as failed because of an internal error resolving the graph."
            )
            resolution_status = ResolutionStatus.FAILED

        self._move_runs_to_terminal_state(reason)
        self._update_resolution_status(resolution_status)
        self._notify_pipeline_update()

    def _move_runs_to_terminal_state(self, reason):
        for run_id, run in self._runs.items():
            state = FutureState.as_object(run.future_state)
            if state.is_terminal():
                continue
            run.future_state = FutureState.FAILED
            run.exception = reason
            self._buffer_runs[run_id] = run
        self._save_graph()

    def _update_resolution_status(self, status: ResolutionStatus):
        resolution = api_client.get_resolution(self._root_future.id)
        resolution.status = status
        api_client.save_resolution(resolution)

    def _get_run(self, run_id) -> Run:
        # Should refresh from DB for remote exec
        return self._runs[run_id]

    def _add_run(self, run: Run):
        self._runs[run.id] = run
        self._buffer_runs[run.id] = run

    def _add_artifact(self, artifact: Artifact):
        self._artifacts[artifact.id] = artifact
        self._buffer_artifacts[artifact.id] = artifact

    def _add_edge(self, edge: Edge):
        edge_key = make_edge_key(edge)
        self._edges[edge_key] = edge
        self._buffer_edges[edge_key] = edge

    def _populate_graph(
        self,
        future: AbstractFuture,
        input_artifacts: Optional[Dict[str, Artifact]] = None,
        output_artifact: Optional[Artifact] = None,
    ) -> Run:
        """
        Update the graph based on future.
        """
        if future.id not in self._runs:
            run = make_run_from_future(future)
            run.root_id = self._futures[0].id
            self._add_run(run)

        # Updating input edges
        for name, value in future.kwargs.items():
            # Updating the input artifact
            artifact_id = None
            if input_artifacts is not None and name in input_artifacts:
                artifact_id = input_artifacts[name].id

            # If the input is a future, we connect the edge
            source_run_id = None
            if isinstance(value, AbstractFuture):
                source_run_id = value.id

            # Attempt to link edges across nested graphs
            # This relies on value identity, it's ok for complex objects
            # but `a is a` is true for e.g. int, but `a` may not be the value passed in
            # from the parent input.
            # The parent_id field is currently not used in the DAG view.
            parent_id = None

            if future.parent_future is not None:
                for (
                    parent_name,
                    parent_value,
                ) in future.parent_future.resolved_kwargs.items():
                    if value is parent_value:
                        parent_edge = self._get_input_edge(
                            destination_run_id=future.parent_future.id,
                            destination_name=parent_name,
                        )
                        if parent_edge is None:
                            raise RuntimeError("Missing parent edge")

                        parent_id = parent_edge.id

            # This is idempotent, edges are indexed by a unique key.
            # It's ok to set the same edge multiple times (e.g. first without
            # `artifact_id`, then with)
            self._update_edge(
                source_run_id=source_run_id,
                destination_run_id=future.id,
                destination_name=name,
                artifact_id=artifact_id,
                parent_id=parent_id,
            )

        # Updating output edges

        # Updating the output artifact
        artifact_id = None
        if output_artifact is not None:
            artifact_id = output_artifact.id

        # There can be multiple output edges:
        # - the output value is input to multiple futures
        # - the future is nested and the parent future has multiple output edges
        output_edges = self._get_output_edges(future.id)

        # It means we are creating it for the first time
        if len(output_edges) == 0:
            # Let's figure out if the parent future has output edges yet
            parent_output_edges = []

            if (
                future.parent_future is not None
                and future.parent_future.nested_future is future
            ):
                parent_output_edges = self._get_output_edges(future.parent_future.id)

            parent_ids: Union[List[str], Tuple[None]] = [
                edge.id for edge in parent_output_edges
            ] or (None,)

            # For each parent output edge, we create an edge
            for parent_id in parent_ids:
                self._update_edge(
                    source_run_id=future.id,
                    destination_run_id=None,
                    destination_name=None,
                    artifact_id=artifact_id,
                    parent_id=parent_id,
                )
        # There already are output edges, we simply update the artifact id
        else:
            for output_edge in output_edges:
                self._update_edge(
                    source_run_id=future.id,
                    destination_run_id=output_edge.destination_run_id,
                    destination_name=output_edge.destination_name,
                    parent_id=output_edge.parent_id,
                    artifact_id=artifact_id,
                )

        # populate the graph for upstream futures
        for value in future.kwargs.values():
            if isinstance(value, AbstractFuture):
                self._populate_graph(value)

        return self._runs[future.id]

    def _save_graph(self):
        """
        Persist the graph to the DB
        """
        runs = list(self._buffer_runs.values())
        artifacts = list(self._buffer_artifacts.values())
        edges = list(self._buffer_edges.values())

        if not any(len(buffer) for buffer in (runs, artifacts, edges)):
            return

        api_client.save_graph(
            root_id=self._futures[0].id, runs=runs, artifacts=artifacts, edges=edges
        )

        self._buffer_runs.clear()
        self._buffer_artifacts.clear()
        self._buffer_edges.clear()


def make_edge_key(edge: Edge) -> str:
    return "{}:{}:{}:{}".format(
        edge.source_run_id,
        edge.parent_id,
        edge.destination_run_id,
        edge.destination_name,
    )
