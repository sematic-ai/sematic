# Standard library
import datetime
from typing import Dict, Optional
import uuid

# Glow
from glow.abstract_future import AbstractFuture, FutureState
from glow.db.models.artifact import Artifact
from glow.db.models.edge import Edge
from glow.db.models.run import Run
from glow.resolvers.state_machine_resolver import StateMachineResolver
from glow.db.models.factories import make_artifact, make_run_from_future
from glow.db.queries import save_graph


class OfflineResolver(StateMachineResolver):
    """
    A resolver to resolver a DAG locally.
    """

    def __init__(self):
        super().__init__()
        self._edges: Dict[str, Edge] = {}
        self._runs: Dict[str, Run] = {}
        self._artifacts: Dict[str, Artifact] = {}

    def _set_edge(
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
        edge_key = "{}:{}:{}".format(
            source_run_id, destination_run_id, destination_name
        )

        edge = self._edges.get(edge_key)

        if edge is None:
            edge = Edge(
                source_run_id=source_run_id,
                destination_run_id=destination_run_id,
                destination_name=destination_name,
                artifact_id=artifact_id,
                parent_id=parent_id,
            )

        # We don't want to overwrite
        if artifact_id is not None:
            edge.artifact_id = artifact_id

        self._edges[edge_key] = edge

    def _get_input_edge(self, destination_run_id, destination_name) -> Optional[Edge]:
        """
        Find an input edge.
        """
        for key, edge in self._edges.items():
            # Kind of ugly heh
            if key.endswith(":{}:{}".format(destination_run_id, destination_name)):
                return edge

        return None

    def _get_output_edge(self, source_run_id) -> Optional[Edge]:
        """
        Find an output edge.
        """
        for key, edge in self._edges.items():
            if key.startswith("{}:".format(source_run_id)):
                return edge

        return None

    def _schedule_future(self, future: AbstractFuture) -> None:
        self._run_inline(future)

    def _run_inline(self, future: AbstractFuture) -> None:
        self._set_future_state(future, FutureState.SCHEDULED)
        try:
            value = future.calculator.calculate(**future.resolved_kwargs)
            cast_value = future.calculator.cast_output(value)
            self._update_future_with_value(future, cast_value)
        except Exception as exception:
            self._handle_future_failure(future, exception)

    def _wait_for_scheduled_run(self) -> None:
        pass

    def _future_will_schedule(self, future: AbstractFuture) -> None:
        super()._future_will_schedule(future)

        input_artifacts = {
            name: make_artifact(value, future.calculator.input_types[name])
            for name, value in future.resolved_kwargs.items()
        }

        run = self._populate_graph(future, input_artifacts=input_artifacts)

        run.future_state = FutureState.SCHEDULED
        run.root_id = self._futures[0].id
        run.started_at = datetime.datetime.utcnow()

        self._save_graph()

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

        self._save_graph()

    def _future_did_resolve(self, future: AbstractFuture) -> None:
        super()._future_did_resolve(future)

        output_artifact = make_artifact(future.value, future.calculator.output_type)

        self._populate_graph(future, output_artifact=output_artifact)

        self._save_graph()

    def _future_did_fail(self, failed_future: AbstractFuture) -> None:
        super()._future_did_fail(failed_future)

        run = self._get_run(failed_future.id)

        run.future_state = (
            FutureState.NESTED_FAILED
            if failed_future.nested_future is not None
            and failed_future.state in (FutureState.FAILED, FutureState.NESTED_FAILED)
            else FutureState.FAILED
        )
        run.failed_at = datetime.datetime.utcnow()

        self._save_graph()

    def _get_run(self, run_id) -> Run:
        # Should refresh from DB for remote exec
        return self._runs[run_id]

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
            self._runs[future.id] = run

        for name, value in future.kwargs.items():
            artfact_id = None
            if input_artifacts is not None and name in input_artifacts:
                artfact_id = input_artifacts[name].id
                self._artifacts[artfact_id] = input_artifacts[name]

            source_run_id = None
            if isinstance(value, AbstractFuture):
                source_run_id = value.id

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

            self._set_edge(
                source_run_id=source_run_id,
                destination_run_id=future.id,
                destination_name=name,
                artifact_id=artfact_id,
                parent_id=parent_id,
            )

        destination_run_id, destination_name = None, None
        output_edge = self._get_output_edge(future.id)
        if output_edge is not None:
            destination_run_id = output_edge.destination_run_id
            destination_name = output_edge.destination_name
            parent_id = output_edge.parent_id

        artifact_id = None
        if output_artifact is not None:
            artifact_id = output_artifact.id
            self._artifacts[artifact_id] = output_artifact

        parent_id = None
        if (
            future.parent_future is not None
            and future.parent_future.nested_future is future
        ):
            parent_edge = self._get_output_edge(future.parent_future.id)
            if parent_edge is not None:
                parent_id = parent_edge.id

        self._set_edge(
            source_run_id=future.id,
            destination_run_id=destination_run_id,
            destination_name=destination_name,
            artifact_id=artifact_id,
            parent_id=parent_id,
        )

        for value in future.kwargs.values():
            if isinstance(value, AbstractFuture):
                self._populate_graph(value)

        return self._runs[future.id]

    def _save_graph(self):
        """
        Persist the graph to the DB
        """
        save_graph(
            runs=self._runs.values(),
            artifacts=self._artifacts.values(),
            edges=self._edges.values(),
        )
