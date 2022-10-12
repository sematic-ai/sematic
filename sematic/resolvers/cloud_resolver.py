# Standard Library
import logging
import time
from typing import Dict, List, Optional

# Third-party
import cloudpickle

# Sematic
import sematic.api_client as api_client
import sematic.storage as storage
from sematic.abstract_future import AbstractFuture, FutureState
from sematic.container_images import get_image_uri
from sematic.db.models.artifact import Artifact
from sematic.db.models.edge import Edge
from sematic.db.models.factories import get_artifact_value
from sematic.db.models.resolution import ResolutionKind
from sematic.db.models.run import Run
from sematic.resolvers.local_resolver import LocalResolver, make_edge_key
from sematic.utils.exceptions import format_exception_for_run

logger = logging.getLogger(__name__)


_MAX_DELAY_BETWEEN_STATUS_UPDATES_SECONDS = 600  # 600s => 10 min
_DELAY_BETWEEN_STATUS_UPDATES_BACKOFF = 1.5

# It is important not to change these! They are used for identifying the start/end of
# inline run logs. If you change it, inline logs written with prior versions of Sematic
# might not be readable for new versions of Sematic.
START_INLINE_RUN_INDICATOR = "--------- Sematic Start Inline Run {} ---------"
END_INLINE_RUN_INDICATOR = "--------- Sematic End Inline Run {} ---------"


class CloudResolver(LocalResolver):
    """
    Resolves a pipeline on a Kubernetes cluster.

    Parameters
    ----------
    detach: Optional[bool]
        Defaults to `True`.

        When `True`, the driver job will run on the remote cluster. This is the so
        called `fire-and-forget` mode. The shell prompt will return as soon as
        the driver job as been submitted.

        When `False`, the driver job runs on the local machine. The shell prompt
        will return when the entire pipeline has completed.
    """

    def __init__(self, detach: bool = True, is_running_remotely: bool = False):
        super().__init__(detach=detach)

        # TODO: Replace this with a cloud storage engine
        self._store_artifacts = True

        self._output_artifacts_by_run_id: Dict[str, Artifact] = {}
        self._is_running_remotely = is_running_remotely

    def set_graph(self, runs: List[Run], artifacts: List[Artifact], edges: List[Edge]):
        """
        Set the graph to an existing graph.

        This is mostly used in `worker.py` to be able to start from previously created
        graph.
        """
        if len(self._runs) > 0:
            raise RuntimeError("Cannot override a graph")

        self._runs = {run.id: run for run in runs}
        self._artifacts = {artifact.id: artifact for artifact in artifacts}
        self._edges = {make_edge_key(edge): edge for edge in edges}

    def _get_resolution_image(self) -> Optional[str]:
        return get_image_uri()

    def _get_resolution_kind(self, detached) -> ResolutionKind:
        return ResolutionKind.KUBERNETES if detached else ResolutionKind.LOCAL

    def _create_resolution(self, root_future, detached):
        if self._is_running_remotely:
            # resolution should have been created prior to the resolver
            # actually starting its remote resolution.
            return
        super()._create_resolution(root_future, detached)

    def _update_run_and_future_pre_scheduling(self, run: Run, future: AbstractFuture):
        # For the cloud resolver, the server will update the relevant
        # run fields when it gets scheduled by the server.
        pass

    def _detach_resolution(self, future: AbstractFuture) -> str:
        run = self._populate_run_and_artifacts(future)
        self._save_graph()
        self._create_resolution(future, detached=True)
        run.root_id = future.id

        api_client.notify_pipeline_update(run.calculator_path)

        # SUBMIT RESOLUTION JOB
        api_client.schedule_resolution(future.id)

        return run.id

    def _schedule_future(self, future: AbstractFuture) -> None:
        run = api_client.schedule_run(future.id)
        self._runs[run.id] = run
        self._set_future_state(future, FutureState[run.future_state])  # type: ignore

    def _wait_for_scheduled_run(self) -> None:
        run_id = self._wait_for_any_inline_run() or self._wait_for_any_remote_job()

        if run_id is None:
            return

        self._process_run_output(run_id)

    def _process_run_output(self, run_id: str):
        self._refresh_graph(run_id)

        run = self._get_run(run_id)

        future = next(future for future in self._futures if future.id == run.id)

        if run.future_state not in {FutureState.RESOLVED.value, FutureState.RAN.value}:
            self._handle_future_failure(
                future, Exception("Run failed, see exception in the UI."), run.exception
            )
            return

        if run.nested_future_id is not None:
            pickled_nested_future = storage.get(
                make_nested_future_storage_key(run.nested_future_id)
            )
            value = cloudpickle.loads(pickled_nested_future)

        else:
            output_edge = self._get_output_edges(run.id)[0]
            output_artifact = self._artifacts[output_edge.artifact_id]
            self._output_artifacts_by_run_id[run.id] = output_artifact
            value = get_artifact_value(output_artifact)

        self._update_future_with_value(future, value)

    def _get_output_artifact(self, run_id: str) -> Optional[Artifact]:
        return self._output_artifacts_by_run_id.get(run_id)

    def _future_did_fail(self, failed_future: AbstractFuture) -> None:
        # Unlike LocalResolver._future_did_fail, we only care about
        # failing parent futures since runs are marked FAILED by worker.py
        run = self._get_run(failed_future.id)
        if (
            failed_future.state == FutureState.FAILED
            and run is not None
            and run.exception is None
        ):
            run.exception = format_exception_for_run()
        self._add_run(run)
        self._save_graph()
        if failed_future.state == FutureState.NESTED_FAILED:
            super()._future_did_fail(failed_future)

    def _refresh_graph(self, run_id: str):
        """
        Refresh graph for run ID.

        Will only refresh artifacts and edges directly connected to run
        """
        runs, artifacts, edges = api_client.get_graph(run_id)

        for run in runs:
            self._runs[run.id] = run

        for artifact in artifacts:
            self._artifacts[artifact.id] = artifact

        for edge in edges:
            self._edges[make_edge_key(edge)] = edge

    def _wait_for_any_inline_run(self) -> Optional[str]:
        return next(
            (
                future.id
                for future in self._futures
                if future.props.inline and future.state == FutureState.SCHEDULED
            ),
            None,
        )

    def _wait_for_any_remote_job(self) -> Optional[str]:
        scheduled_futures_by_id: Dict[str, AbstractFuture] = {
            future.id: future
            for future in self._futures
            if not future.props.inline and future.state == FutureState.SCHEDULED
        }

        if len(scheduled_futures_by_id) == 0:
            logger.info("No futures to wait on")
            return None

        delay_between_updates = 1.0
        while True:
            updated_states: Dict[
                str, FutureState
            ] = api_client.update_run_future_states(
                list(scheduled_futures_by_id.keys())
            )
            logger.info("Checking for updates on %s", scheduled_futures_by_id.keys())
            for run_id, new_state in updated_states.items():
                future = scheduled_futures_by_id[run_id]
                if new_state != FutureState.SCHEDULED:
                    # no need to actually update the future's state here, that will
                    # be handled by the post-processing logic once it is aware this
                    # future has changed
                    self._refresh_graph(future.id)
                    return future.id

            logger.info("Sleeping for %s s", delay_between_updates)
            time.sleep(delay_between_updates)
            delay_between_updates = min(
                _MAX_DELAY_BETWEEN_STATUS_UPDATES_SECONDS,
                _DELAY_BETWEEN_STATUS_UPDATES_BACKOFF * delay_between_updates,
            )

    def _start_inline_execution(self, future_id):
        """Callback called before an inline execution"""
        logger.info(START_INLINE_RUN_INDICATOR.format(future_id))

    def _end_inline_execution(self, future_id):
        """Callback called at the end of an inline execution"""
        logger.info(END_INLINE_RUN_INDICATOR.format(future_id))


def make_nested_future_storage_key(future_id: str) -> str:
    return "futures/{}".format(future_id)
