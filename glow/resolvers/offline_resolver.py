# Standard library
import datetime
from typing import Dict, Optional, List, Union, Tuple

# Third-party
# import requests

# Glow
from glow.abstract_future import AbstractFuture, FutureState
from glow.db.models.artifact import Artifact
from glow.db.models.edge import Edge
from glow.db.models.run import Run
from glow.resolvers.state_machine_resolver import StateMachineResolver
from glow.db.models.factories import make_artifact, make_run_from_future
from glow.db.queries import save_graph
import glow.api_client as api_client


class OfflineResolver(StateMachineResolver):
    """
    A resolver to resolver a DAG locally.
    """

    def __init__(self):
        super().__init__()
        self._edges: Dict[str, Edge] = {}
        self._runs: Dict[str, Run] = {}
        self._artifacts: Dict[str, Artifact] = {}

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
        edge_key = "{}:{}:{}:{}".format(
            source_run_id, parent_id, destination_run_id, destination_name
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

    def _get_output_edges(self, source_run_id) -> List[Edge]:
        """
        Find output edges.
        There can be multiple ones if the output goes to multiple futures.
        """
        return [
            edge
            for key, edge in self._edges.items()
            if key.startswith("{}:".format(source_run_id))
        ]

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

    def _future_did_schedule(self, future: AbstractFuture) -> None:
        super()._future_did_schedule(future)
        root_future = self._futures[0]
        if root_future.id == future.id:
            api_client.notify_pipeline_start(self._runs[future.id].calculator_path)

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
        if future.id == self._futures[0].id:
            print(self._edges)

    def _future_did_resolve(self, future: AbstractFuture) -> None:
        super()._future_did_resolve(future)

        run = self._get_run(future.id)
        run.future_state = FutureState.RESOLVED
        run.resolved_at = datetime.datetime.utcnow()

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

        # Updating input edges
        for name, value in future.kwargs.items():
            # Updating the input artifact
            artifact_id = None
            if input_artifacts is not None and name in input_artifacts:
                artifact_id = input_artifacts[name].id
                self._artifacts[artifact_id] = input_artifacts[name]

            # If the input is a future, we connect the edge
            source_run_id = None
            if isinstance(value, AbstractFuture):
                source_run_id = value.id

            if future.name == "evaluate_model" and name == "model":
                print(
                    "evaluate_model",
                    "model",
                    future.state,
                    isinstance(value, AbstractFuture),
                )
                print(source_run_id)

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
            self._artifacts[artifact_id] = output_artifact

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
        save_graph(
            runs=self._runs.values(),
            artifacts=self._artifacts.values(),
            edges=self._edges.values(),
        )
        api_client.notify_graph_update(self._futures[0].id)


"""
{
    "a57bf979d18743649945455b9e22f379": Run(
        id="a57bf979d18743649945455b9e22f379",
        future_state="RAN",
        name="PyTorch MNIST Example",
        calculator_path="glow.examples.mnist.pytorch.calculators.pipeline",
        parent_id=None,
        root_id="a57bf979d18743649945455b9e22f379",
    ),
    "56a46997970448119e0483f0b9e238b9": Run(
        id="56a46997970448119e0483f0b9e238b9",
        future_state="CREATED",
        name="evaluate_model",
        calculator_path="glow.examples.mnist.pytorch.calculators.evaluate_model",
        parent_id="a57bf979d18743649945455b9e22f379",
        root_id="a57bf979d18743649945455b9e22f379",
        description="Evaluate the model.",
    ),
    "adade426535e4cce9fdff87d484abd4d": Run(
        id="adade426535e4cce9fdff87d484abd4d",
        future_state="CREATED",
        name="train_model",
        calculator_path="glow.examples.mnist.pytorch.calculators.train_model",
        parent_id="a57bf979d18743649945455b9e22f379",
        root_id="a57bf979d18743649945455b9e22f379",
    ),
    "80e59e6e92c34420bb7481610fde6e49": Run(
        id="80e59e6e92c34420bb7481610fde6e49",
        future_state="CREATED",
        name="get_dataloader",
        calculator_path="glow.examples.mnist.pytorch.calculators.get_dataloader",
        parent_id="a57bf979d18743649945455b9e22f379",
        root_id="a57bf979d18743649945455b9e22f379",
    ),
    "2287a784a45d40cf9881646b52e235f0": Run(
        id="2287a784a45d40cf9881646b52e235f0",
        future_state="CREATED",
        name="get_dataloader",
        calculator_path="glow.examples.mnist.pytorch.calculators.get_dataloader",
        parent_id="a57bf979d18743649945455b9e22f379",
        root_id="a57bf979d18743649945455b9e22f379",
    ),
}
{
    "None:None:a57bf979d18743649945455b9e22f379:config": Edge(
        id="31799db684b34b7c91075a07c13adc5f",
        source_run_id=None,
        source_name=None,
        destination_run_id="a57bf979d18743649945455b9e22f379",
        destination_name="config",
        artifact_id="9c1597e395db5467ecdc773ce27bbb79acfc9c20",
        parent_id=None,
    ),
    "a57bf979d18743649945455b9e22f379:None:None:None": Edge(
        id="80d24d6efadb442cb1d8124ea1665a5b",
        source_run_id="a57bf979d18743649945455b9e22f379",
        source_name=None,
        destination_run_id=None,
        destination_name=None,
        artifact_id=None,
        parent_id=None,
    ),
    "adade426535e4cce9fdff87d484abd4d:None:56a46997970448119e0483f0b9e238b9:model": Edge(
        id="13dd05b841f34d4e9c1351a56d096514",
        source_run_id="adade426535e4cce9fdff87d484abd4d",
        source_name=None,
        destination_run_id="56a46997970448119e0483f0b9e238b9",
        destination_name="model",
        artifact_id=None,
        parent_id=None,
    ),
    "2287a784a45d40cf9881646b52e235f0:None:56a46997970448119e0483f0b9e238b9:test_loader": Edge(
        id="db50bf42ee224ff2b904b43db1fbec30",
        source_run_id="2287a784a45d40cf9881646b52e235f0",
        source_name=None,
        destination_run_id="56a46997970448119e0483f0b9e238b9",
        destination_name="test_loader",
        artifact_id=None,
        parent_id=None,
    ),
    "None:None:56a46997970448119e0483f0b9e238b9:device": Edge(
        id="072cf8175f104030bc61885ec420a139",
        source_run_id=None,
        source_name=None,
        destination_run_id="56a46997970448119e0483f0b9e238b9",
        destination_name="device",
        artifact_id=None,
        parent_id=None,
    ),
    "56a46997970448119e0483f0b9e238b9:80d24d6efadb442cb1d8124ea1665a5b:None:None": Edge(
        id="43b2bea76de24879aa18075079a11c72",
        source_run_id="56a46997970448119e0483f0b9e238b9",
        source_name=None,
        destination_run_id=None,
        destination_name=None,
        artifact_id=None,
        parent_id="80d24d6efadb442cb1d8124ea1665a5b",
    ),
    "None:None:adade426535e4cce9fdff87d484abd4d:config": Edge(
        id="e60f4e5e075c479cafe229a0364ec367",
        source_run_id=None,
        source_name=None,
        destination_run_id="adade426535e4cce9fdff87d484abd4d",
        destination_name="config",
        artifact_id=None,
        parent_id=None,
    ),
    "80e59e6e92c34420bb7481610fde6e49:None:adade426535e4cce9fdff87d484abd4d:train_loader": Edge(
        id="357833fa29604a65ad2a9654fede5542",
        source_run_id="80e59e6e92c34420bb7481610fde6e49",
        source_name=None,
        destination_run_id="adade426535e4cce9fdff87d484abd4d",
        destination_name="train_loader",
        artifact_id=None,
        parent_id=None,
    ),
    "None:None:adade426535e4cce9fdff87d484abd4d:device": Edge(
        id="f11b8feebac44dc588969bce9b761c32",
        source_run_id=None,
        source_name=None,
        destination_run_id="adade426535e4cce9fdff87d484abd4d",
        destination_name="device",
        artifact_id=None,
        parent_id=None,
    ),
    "a1212b888b354d09a047f1eb0d65bbf5:None:80e59e6e92c34420bb7481610fde6e49:dataset": Edge(
        id="e5c8f999b9304b0c8b4b39803dbff1fe",
        source_run_id="a1212b888b354d09a047f1eb0d65bbf5",
        source_name=None,
        destination_run_id="80e59e6e92c34420bb7481610fde6e49",
        destination_name="dataset",
        artifact_id=None,
        parent_id=None,
    ),
    "None:None:80e59e6e92c34420bb7481610fde6e49:config": Edge(
        id="bcb9e6c1ead34cbf826cede2dbd88a1f",
        source_run_id=None,
        source_name=None,
        destination_run_id="80e59e6e92c34420bb7481610fde6e49",
        destination_name="config",
        artifact_id=None,
        parent_id=None,
    ),
    "None:None:a1212b888b354d09a047f1eb0d65bbf5:train": Edge(
        id="c66f18e92aa54946b29c554c62206c10",
        source_run_id=None,
        source_name=None,
        destination_run_id="a1212b888b354d09a047f1eb0d65bbf5",
        destination_name="train",
        artifact_id=None,
        parent_id=None,
    ),
    "None:None:a1212b888b354d09a047f1eb0d65bbf5:path": Edge(
        id="6939d6e89b1242668797ca2cdeb1610e",
        source_run_id=None,
        source_name=None,
        destination_run_id="a1212b888b354d09a047f1eb0d65bbf5",
        destination_name="path",
        artifact_id=None,
        parent_id=None,
    ),
    "f5e26bb847e54160963ba9f4c004c082:None:2287a784a45d40cf9881646b52e235f0:dataset": Edge(
        id="44a072530390438b8733f8de587b58c9",
        source_run_id="f5e26bb847e54160963ba9f4c004c082",
        source_name=None,
        destination_run_id="2287a784a45d40cf9881646b52e235f0",
        destination_name="dataset",
        artifact_id=None,
        parent_id=None,
    ),
    "None:None:2287a784a45d40cf9881646b52e235f0:config": Edge(
        id="21a114f5934e486ab07f0c643cdf2e5d",
        source_run_id=None,
        source_name=None,
        destination_run_id="2287a784a45d40cf9881646b52e235f0",
        destination_name="config",
        artifact_id=None,
        parent_id=None,
    ),
    "None:None:f5e26bb847e54160963ba9f4c004c082:train": Edge(
        id="a1f1f78f87a6466290e0c878f5724a57",
        source_run_id=None,
        source_name=None,
        destination_run_id="f5e26bb847e54160963ba9f4c004c082",
        destination_name="train",
        artifact_id=None,
        parent_id=None,
    ),
    "None:None:f5e26bb847e54160963ba9f4c004c082:path": Edge(
        id="b41e4ba83b4747f7b2e129d2e9eb7407",
        source_run_id=None,
        source_name=None,
        destination_run_id="f5e26bb847e54160963ba9f4c004c082",
        destination_name="path",
        artifact_id=None,
        parent_id=None,
    ),
}
"""
