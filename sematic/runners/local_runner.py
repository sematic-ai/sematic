# Standard Library
import datetime
import logging
import os
import signal
import uuid
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Union

# Third-party
import socketio  # type: ignore

# Sematic
import sematic.api_client as api_client
from sematic.abstract_function import FunctionError
from sematic.abstract_future import AbstractFuture, FutureState
from sematic.caching import (
    CacheNamespace,
    determine_cache_namespace,
    get_future_cache_key,
)
from sematic.config.config import get_config
from sematic.config.user_settings import get_active_user_settings_strings
from sematic.db.models.artifact import Artifact
from sematic.db.models.edge import Edge
from sematic.db.models.factories import make_artifact, make_run_from_future
from sematic.db.models.git_info import GitInfo
from sematic.db.models.resolution import PipelineRun, PipelineRunKind, PipelineRunStatus
from sematic.db.models.run import Run
from sematic.graph import FutureGraph, Graph, RerunMode
from sematic.plugins.abstract_builder import get_build_config, get_run_command
from sematic.resolvers.resource_managers.server_manager import ServerResourceManager
from sematic.resolvers.resource_requirements import ResourceRequirements
from sematic.runners.silent_runner import SilentRunner
from sematic.utils.exceptions import ExceptionMetadata, format_exception_for_run
from sematic.utils.git import get_git_info
from sematic.utils.retry import retry_call
from sematic.versions import CURRENT_VERSION_STR

logger = logging.getLogger(__name__)


class LocalRunner(SilentRunner):
    """
    A `Runner` that runs a pipeline locally.

    Each `Future`'s execution is tracked in the DB as a run. Each individual function's
    input argument and output value is tracked as an `Artifact`.

    Parameters
    ----------
    cache_namespace: CacheNamespace
        A string or a `Callable` which takes a root `Future` and returns a string, which
        will be used as the cache key namespace in which the executed funcs' outputs will
        be cached, as long as they also have the `cache` flag activated. Defaults to
        `None`.

        The `Callable` option takes as input the pipeline run's root `Future`. All the
        other required variables must be enclosed in the `Callables`' context. The
        `Callable` must have a small memory footprint and must return immediately!
    rerun_from: Optional[str]
        When `None`, the pipeline is executed from scratch, as normally. When not `None`,
        must be the id of a `Run` from a previous pipeline run. The nature of the rerun
        when an id is specified will depend on the `rerun_mode` parameter.
    rerun_mode: RerunMode
        This option is only used when `rerun_from` has been given a run id.
        If set to
        `RerunMode.SPECIFIC_RUN` (the default):
            Instead of running from scratch, parts of that previous
            pipeline run will be cloned up until the specific `Run`, and only the
            specified `Run`, nested and downstream `Future`s will be executed.
            This is meant to be used for retries or for hotfixes, without needing to
            re-run the entire pipeline again.
        `RerunMode.CONTINUE`:
            In this case, the run id passed to rerun_from must be the root id of a
            pipeline run. The new pipeline run will use any available results from the
            old one and only execute what is necessary to determine the final result.
            The new pipeline run will use a NEW future graph, cloned from the old one.
        `RerunMode.REENTER`:
            In this case, the run id passed to rerun_from must be the root id of the
            pipeline run. The new pipeline run will use any available results from the
            old one and only execute what is necessary to determine the final result.
            The new pipeline run will use the EXISTING future graph, recreated from
            the runs in the DB.
    """

    _resource_manager: Optional[ServerResourceManager] = None  # type: ignore

    def __init__(
        self,
        cache_namespace: Optional[CacheNamespace] = None,
        rerun_from: Optional[str] = None,
        rerun_mode: Optional[RerunMode] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self._edges: Dict[str, Edge] = {}
        self._runs: Dict[str, Run] = {}
        self._artifacts: Dict[str, Artifact] = {}

        self._pipeline_run_was_created = False

        # A cache of already created artifacts to avoid making them over again.
        # The key is run ID, the value is a dictionary where the key is input
        # name, or None for output and the value is the artifact.
        self._artifacts_by_run_id: Dict[
            str, Dict[Optional[str], Artifact]
        ] = defaultdict(dict)

        # Buffers for persistence
        self._buffer_edges: Dict[str, Edge] = {}
        self._buffer_runs: Dict[str, Run] = {}
        self._buffer_artifacts: Dict[str, Artifact] = {}

        self._sio_client = socketio.Client()

        self._rerun_from_run_id = rerun_from
        self._rerun_mode = rerun_mode

        # this parameter needs to be determined after the root future is
        # enqueued and before the pipeline run is created
        self._cache_namespace_str: Optional[str] = None
        self._raw_cache_namespace = cache_namespace

        # cached git info if it is known from a source other than local git execution
        self._git_info: Optional[GitInfo] = None

    def _seed_graph(self, future: AbstractFuture):
        if self._rerun_from_run_id is None:
            super()._seed_graph(future)
        else:
            self._seed_from_existing(future, self._rerun_from_run_id, self._rerun_mode)

    def _reenter_inline_runs(self, futures, runs):
        """During runner reentry, correct the state of any inline futures/runs.

        A correction may be needed if the future was executing in the runner when the
        runner restarted. In this case, this method will mark the future and run for
        retry. The update to the future and run happen in-place.
        """
        for future in futures:
            if not future.props.standalone and future.state == FutureState.SCHEDULED:
                # The future was executing in the runner when the runner restarted.
                # So we need to start it again.
                logger.warning(
                    "The future %s was executing in the runner when the runner "
                    "restarted. Restarting execution of the future. "
                    "Some of the future's properties may have changed "
                    "(see Issue #1032)",
                    future.id,
                )
                future.state = FutureState.RETRYING
                inline_run = next(run for run in runs if run.id == future.id)
                inline_run.future_state = FutureState.RETRYING
                api_client.save_graph(
                    self._root_future.id, runs=[inline_run], artifacts=[], edges=[]
                )

    def _seed_from_existing(
        self, future: AbstractFuture, from_run_id: str, rerun_mode: Optional[RerunMode]
    ):
        """
        Instead of simply queuing the root future, this method seeds the future graph
        from an existing execution. This execution may be another execution of
        same pipeline, or it may be the same execution of that pipeline that originated
        from an earlier runner pod (if the runner pod has restarted).
        """
        rerun_mode = rerun_mode or RerunMode.SPECIFIC_RUN

        try:
            run = api_client.get_run(from_run_id)
        except api_client.ResourceNotFoundError as e:
            raise ValueError(
                f"Cannot restart from {from_run_id}: run cannot be found."
            ) from e

        if rerun_mode is RerunMode.CONTINUE and run.id != run.root_id:
            raise ValueError("Cannot use RerunMode.CONTINUE with a non-root run.")
        elif rerun_mode is RerunMode.REENTER and run.id != future.id:
            # This should be impossible. Raise a helpful message in case
            # it ever happens anyway.
            raise ValueError(
                f"Seeding from the DB for a reentered runner requires that "
                f"The root future id ('{future.id}') must match the rerun id "
                f"('{run.id}')."
            )

        runs, artifacts, edges = api_client.get_graph(run.root_id, root=True)

        graph = Graph(
            runs=runs,
            artifacts=artifacts,
            edges=edges,
        )

        if not graph.input_artifacts_ready(run.id):
            raise ValueError(
                f"Cannot start from {from_run_id}: upstream runs did not succeed."
            )

        logger.info(f"Attempting to rerun from {from_run_id}")

        is_clone = False
        if rerun_mode is RerunMode.SPECIFIC_RUN:
            future_graph: FutureGraph = graph.clone_futures(
                reset_from=from_run_id,
            )
            is_clone = True
        elif rerun_mode is RerunMode.CONTINUE:
            future_graph = graph.clone_futures()
            is_clone = True
        elif rerun_mode is RerunMode.REENTER:
            future_graph = graph.to_future_graph()
        else:
            raise ValueError(f"Unrecognized rerun mode: {rerun_mode}")

        if is_clone:
            # Making sure we honor id of future passed from the outside
            future_graph.set_root_future_id(future.id)  # type: ignore

        self._futures = list(future_graph.futures_by_run_id.values())

        if rerun_mode == RerunMode.REENTER:
            self._reenter_inline_runs(self._futures, runs)

        # This is necessary, otherwise the root run will not be updated with its
        # cloned status. In detached execution, or rerun, the root run is
        # created outside the runner (either by the server, or by the runner
        # submitting the detached pipeline run from the user's machine).
        self._runs.clear()

        for future in self._futures:
            future.resolved_kwargs = self._get_concrete_kwargs(future)

            if future.state == FutureState.RESOLVED:
                self._artifacts_by_run_id[future.id][
                    None
                ] = future_graph.output_artifacts[future.id]

            if future.state in {FutureState.RESOLVED, FutureState.RAN}:
                for name, artifact in future_graph.input_artifacts[future.id].items():
                    self._artifacts_by_run_id[future.id][name] = artifact

            if is_clone:
                self._populate_graph_from_future(future)

        if not is_clone:
            self._populate_graph_from_objects(runs, artifacts, edges)

        self._save_graph()

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
            raise RuntimeError("Not all input arguments are concrete")

        run = self._populate_graph_from_future(future)

        return run

    def _connect_to_sio_server(self):
        try:
            retry_call(
                f=self._sio_client.connect,
                fargs=[get_config().socket_io_url],
                fkwargs=dict(namespaces=["/pipeline"]),
                delay=1,
                tries=4,
            )
        except BaseException as e:
            # provide the user with useful information, and then continue failing
            logger.exception("Could not connect to the socket.io server", exc_info=e)
            raise

    def _disconnect_from_sio_server(self):
        try:
            retry_call(f=self._sio_client.disconnect, tries=4)
        except BaseException as e:
            # we are shutting down already, so just warn and continue
            logger.warning(
                "Could not cleanly disconnect from the socket.io server: %s", e
            )

    def _pipeline_run_will_start(self) -> None:
        self._connect_to_sio_server()

        @self._sio_client.on("cancel", namespace="/pipeline")
        def _cancel(data):
            if data["resolution_id"] != self._root_future.id:
                return

            logger.warning("Received cancelation event")

            # If we are here, the cancelation should have been applied
            # successfully server-side.

            # Rely on signal handlers to perform the cancellation and cleanup
            # of local resources.
            os.kill(os.getpid(), signal.SIGINT)

        self._populate_run_and_artifacts(self._root_future)
        self._save_graph()
        self._cache_namespace_str = self._make_cache_namespace()
        self._create_pipeline_run(self._root_future)
        if self._rerun_mode != RerunMode.REENTER:
            self._update_pipeline_run_status(PipelineRunStatus.RUNNING)

    def _clean_up_pipeline_run(self, save_graph: bool) -> None:
        self._cancel_non_terminal_futures()
        self._deactivate_all_resources()
        self._disconnect_from_sio_server()
        if save_graph:
            self._save_graph(runs_only=True, retry=False)

        root_run = self._get_run(self._root_future.id)
        pipeline_run = api_client.get_pipeline_run(self._root_future.id)

        status = PipelineRunStatus[pipeline_run.status]  # type: ignore
        if not status.is_terminal():
            if root_run.future_state == FutureState.CANCELED.value:
                pipeline_run.status = PipelineRunStatus.CANCELED
            elif root_run.future_state == FutureState.RESOLVED.value:
                # this method doesn't normally get called for successful runs,
                # but if it does we want it to have the expected behavior.
                pipeline_run.status = PipelineRunStatus.COMPLETE
            else:
                pipeline_run.status = PipelineRunStatus.FAILED
            api_client.save_pipeline_run(pipeline_run)

    def _make_cache_namespace(self) -> Optional[str]:
        """
        Attempts to produce a string cache namespace for the Pipeline Run.

        If the user-supplied cache namespace parameter is:
          - None - returns None
          - a string - returns this string
          - a Callable - invokes it and returns the resulting string

        Must be called after the root future is enqueued, and before the Pipeline Run is
        created.

        Returns
        -------
        A string cache namespace, or None.
        """
        if self._raw_cache_namespace is None:
            logger.debug("The Pipeline Run is not configured to use cached values")
            return None

        try:
            cache_namespace = determine_cache_namespace(
                cache_namespace=self._raw_cache_namespace,
                root_future=self._root_future,
            )

            logger.info(
                "The Pipeline Run will use the cache namespace: %s", cache_namespace
            )

            return cache_namespace

        except Exception:
            logger.warning(
                "The Pipeline Run is unable to use cached values! "
                "Falling back to execution for all funcs!",
                exc_info=1,  # type: ignore
            )
            return None

    def _pipeline_run_did_cancel(self) -> None:
        super()._pipeline_run_did_cancel()
        self._clean_up_pipeline_run(save_graph=True)

    def _read_refreshed_state(self, future: AbstractFuture) -> FutureState:
        run = self._get_run(future.id)
        return FutureState[run.future_state]  # type: ignore

    def _get_tagged_image(self, tag: str) -> Optional[str]:
        return None

    def _create_pipeline_run(self, root_future):
        """Make a Pipeline Run instance and persist it."""
        pipeline_run = self._make_pipeline_run(root_future)
        api_client.save_pipeline_run(pipeline_run)
        self._pipeline_run_was_created = True
        self._notify_pipeline_update()

    def _make_pipeline_run(self, root_future: AbstractFuture) -> PipelineRun:
        """Make a PipelineRun instance."""
        pipeline_run = PipelineRun(
            root_id=root_future.id,
            status=PipelineRunStatus.SCHEDULED,
            kind=PipelineRunKind.LOCAL,
            git_info=self._get_git_info(root_future.function.func),  # type: ignore
            settings_env_vars=get_active_user_settings_strings(),
            client_version=CURRENT_VERSION_STR,
            cache_namespace=self._cache_namespace_str,
            # the user_id is overwritten on the API call based on the user's API key
            user_id=None,
            run_command=get_run_command(),
            build_config=get_build_config(),
        )
        pipeline_run.resource_requirements = self._get_runner_resources()

        return pipeline_run

    def _get_runner_resources(self) -> Optional[ResourceRequirements]:
        return None

    def _get_git_info(self, object: Any) -> Optional[GitInfo]:
        if self._git_info is not None:
            return self._git_info
        return get_git_info(object)

    def _future_will_schedule(self, future: AbstractFuture) -> None:
        super()._future_will_schedule(future)

        run = self._populate_run_and_artifacts(future)
        self._update_run_and_future_pre_scheduling(run, future)
        run.root_id = self._futures[0].id

        self._add_run(run)
        self._save_graph()

    def _update_run_and_future_pre_scheduling(self, run: Run, future: AbstractFuture):
        """Perform any updates to run before saving it to the DB pre-scheduling"""
        future.state = FutureState.SCHEDULED
        run.future_state = FutureState.SCHEDULED
        run.started_at = datetime.datetime.utcnow()

    def _execute_future(self, future: AbstractFuture) -> bool:
        """
        Attempts to execute the given Future.

        If the wrapped func is configured for caching, this function attempts to look up
        an Artifact in the cache for the Run, and directly assigns a concrete value for
        the Future given that artifact, without actually executing the Future.

        Returns true if the future was executed or a cached value was found.
        """
        run = self._get_run(future.id)
        # we are certain all input args are concrete and can compute the cache key
        run.cache_key = self._get_cache_key(future=future)

        if run.cache_key is None:
            return super()._execute_future(future=future)

        # attempt to directly obtain a concrete value for the run based on previous
        # executions:
        try:
            run_results = api_client.get_runs(
                limit=1,  # get the original run
                order="asc",  # it's the oldest
                cache_key=run.cache_key,  # must hit the cache key
                future_state="RESOLVED",  # only resolved runs have associated artifacts
            )

            if len(run_results) == 0:
                logger.debug("Cache key %s did not hit any artifact", run.cache_key)
                return super()._execute_future(future=future)

            original_run = run_results[0]
            _, artifacts, edges = api_client.get_graph(
                run_id=original_run.id, root=False
            )

            # the above query returns all input and output artifacts, so we try to find
            # the artifact which belongs to the run's output value
            original_artifact = self._get_output_artifact(
                run_id=original_run.id, artifacts=artifacts, edges=edges
            )

        except Exception:
            logger.warning(
                "Error fetching an artifact for cache key %s; "
                "Falling back to execution for %s %s",
                run.cache_key,
                future.id,
                future.function,
                exc_info=1,  # type: ignore
            )

            return super()._execute_future(future=future)

        logger.debug(
            "Cache key %s hit run %s with output artifact %s",
            run.cache_key,
            original_run.id,
            original_artifact.id,
        )
        logger.info(
            "Future %s %s will be assigned a value from a cached result",
            future.id,
            future.function,
        )

        # we remember the original artifact in order to reuse it, and not create
        # new copies in the db for each new cached run;
        # the None key corresponds to the run's output artifact
        self._artifacts_by_run_id[run.id][None] = original_artifact

        # _future_did_resolve() will be executed at the end of _update_future_with_value()
        # below, and will re-fetch and overwrite the run in the db;
        # consequently, we need to save the cache_key and original_run fields now;
        # we can only save the run as part of a graph save, so we call _save_graph()
        # TODO: the run is created and updated as a side effect of updating the graph;
        #  the run and future should be atomically updated, if not the same concept;
        #  the run lifecycle should be the main flow the runner deals with, and the
        #  graph should be a consequence of this, without being updated through lateral
        #  effect such as the run is now, and without this disjointed partial save
        run.original_run_id = original_run.id
        self._add_run(run)
        self._save_graph()

        value = api_client.get_artifact_value(artifact=original_artifact)
        self._update_future_with_value(future=future, value=value)
        return True

    def _get_output_artifact(
        self, run_id: str, artifacts: List[Artifact], edges: List[Edge]
    ) -> Artifact:
        for edge in edges:
            if edge.source_run_id == run_id:
                for artifact in artifacts:
                    if artifact.id == edge.artifact_id:
                        return artifact

        raise ValueError(f"Output Artifact not found in Run {run_id} subgraph")

    def _future_did_run(self, future: AbstractFuture) -> None:
        super()._future_did_run(future)

        run = self._get_run(future.id)

        if future.parent_future is not None:
            run.parent_id = future.parent_future.id

        run.future_state = FutureState.RAN
        run.ended_at = datetime.datetime.utcnow()

        if future.nested_future is None:
            raise Exception("Missing nested future")

        run.nested_future_id = future.nested_future.id

        self._populate_graph_from_future(future.nested_future)
        self._add_run(run)
        self._save_graph()

    def _future_did_resolve(self, future: AbstractFuture) -> None:
        super()._future_did_resolve(future)

        run = self._get_run(future.id)
        run.future_state = FutureState.RESOLVED
        run.resolved_at = datetime.datetime.utcnow()

        self._populate_graph_from_future(future)
        self._add_run(run)
        self._save_graph()

    def _future_did_get_marked_for_retry(self, future: AbstractFuture) -> None:
        super()._future_did_get_marked_for_retry(future)

        run = self._get_run(future.id)

        run.future_state = FutureState.RETRYING

        self._add_run(run)
        self._save_graph()

    def _future_did_cancel(self, canceled_future: AbstractFuture) -> None:
        run = self._get_run(canceled_future.id)
        if not FutureState[run.future_state].is_terminal():  # type: ignore
            run.future_state = FutureState.CANCELED.value  # type: ignore
            self._add_run(run)
        self._save_graph(runs_only=True, retry=False)

    def _future_did_fail(self, failed_future: AbstractFuture) -> None:
        super()._future_did_fail(failed_future)

        run = self._get_run(failed_future.id)
        run.future_state = failed_future.state
        run.failed_at = datetime.datetime.utcnow()

        # We do not propagate exceptions to parent runs
        logger.info(
            "Processing failure of run %s, state: %s",
            failed_future.id,
            failed_future.state,
        )

        if run.exception_metadata is None:
            if failed_future.state == FutureState.FAILED:
                run.exception_metadata = format_exception_for_run()
            elif failed_future.state == FutureState.NESTED_FAILED:
                run.exception_metadata = ExceptionMetadata(
                    repr="Failed because the child run failed",
                    name=Exception.__name__,
                    module=Exception.__module__,
                    ancestors=ExceptionMetadata.ancestors_from_exception(Exception),
                )
            # should be unreachable code, here for a sanity check
            else:
                raise RuntimeError(
                    f"Illegal state: future {failed_future.id} in state "
                    f"{failed_future.state} when it should have been already processed"
                )

        self._add_run(run)
        self._save_graph(runs_only=True, retry=False)

    def _notify_pipeline_update(self):
        api_client.notify_pipeline_update(
            self._runs[self._root_future.id].function_path
        )

    def _pipeline_run_did_succeed(self) -> None:
        super()._pipeline_run_did_succeed()
        self._update_pipeline_run_status(PipelineRunStatus.COMPLETE)
        self._notify_pipeline_update()
        self._disconnect_from_sio_server()

    def _pipeline_run_did_fail(
        self, error: Exception, reason: Optional[str] = None
    ) -> None:
        super()._pipeline_run_did_fail(error)

        if isinstance(error, FunctionError):
            reason = reason or (
                "Marked as failed because another run in the graph failed."
            )
            pipeline_run_status = PipelineRunStatus.COMPLETE
        elif isinstance(error, RunnerRestartError):
            reason = reason or (
                "Marked as failed because the runner restarted mid-execution."
            )
            pipeline_run_status = PipelineRunStatus.FAILED
        else:
            reason = reason or (
                "Marked as failed because the rest of the graph failed."
            )
            pipeline_run_status = PipelineRunStatus.FAILED

        self._move_runs_to_terminal_state(reason, fail_root_run=True)
        if self._pipeline_run_was_created:
            self._update_pipeline_run_status(pipeline_run_status)
        else:
            logger.warning(
                "Can't update pipeline run status while handling pipeline run failure, "
                "because pipeline run was never created."
            )
        self._disconnect_from_sio_server()
        self._notify_pipeline_update()

    def _move_runs_to_terminal_state(self, reason, fail_root_run: bool):
        for run_id in self._runs.keys():
            run = self._get_run(run_id)  # may have terminated remotely, re-get from api
            state = FutureState.as_object(run.future_state)

            if state.is_terminal():
                continue

            if run.parent_id is None and fail_root_run:
                # If the pipeline run failed due to an error in the runner
                # itself, it may not yet have a terminal status. We want to
                # make sure the root run gets marked as FAILED instead of
                # CANCELLED in such cases.
                run.future_state = FutureState.FAILED
            else:
                run.future_state = FutureState.CANCELED

            run.failed_at = datetime.datetime.utcnow()

            if run.exception_metadata is None:
                run.exception_metadata = ExceptionMetadata(
                    repr=reason,
                    name=Exception.__name__,
                    module=Exception.__module__,
                    ancestors=ExceptionMetadata.ancestors_from_exception(Exception),
                )

            self._add_run(run)

        self._save_graph(runs_only=True, retry=False)

    def _update_pipeline_run_status(self, status: PipelineRunStatus):
        pipeline_run = api_client.get_pipeline_run(self._root_future.id)
        current_status = PipelineRunStatus[pipeline_run.status]  # type: ignore
        if (
            status == PipelineRunStatus.RUNNING
            and current_status != PipelineRunStatus.SCHEDULED
        ):
            raise RunnerRestartError(
                "It appears that the runner has restarted mid-execution. "
                "The cluster may be under pressure."
            )
        pipeline_run.status = status
        api_client.save_pipeline_run(pipeline_run)

    def _get_run(self, run_id) -> Run:
        run = api_client.get_run(run_id)
        self._runs[run_id] = run
        return run

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

    def _make_run(self, future: AbstractFuture) -> Run:
        """
        Create a Run for the given Future.
        """
        run = make_run_from_future(future=future)
        run.root_id = self._root_future.id

        logger.debug("Created run %s for %s", run.id, future.function)
        return run

    def _get_cache_key(self, future: AbstractFuture) -> Optional[str]:
        """
        Computes a cache key for the specified Future, if configured.
        """
        if self._cache_namespace_str is None:
            return None

        if not future.props.cache:
            logger.debug(
                "Future %s %s is not configured to use the cache",
                future.id,
                future.function,
            )
            return None

        try:
            cache_key = get_future_cache_key(
                cache_namespace=self._cache_namespace_str, future=future
            )
        except Exception:
            logger.warning(
                "Unable to compute the cache key for %s %s",
                future.id,
                future.function,
                exc_info=1,  # type: ignore
            )
            return None

        logger.debug(
            "Future %s %s will use the cache key: %s",
            future.id,
            future.function,
            cache_key,
        )

        return cache_key

    def _make_artifact(
        self, run_id: str, value: Any, type_: Any, name: Optional[str]
    ) -> Artifact:
        # _artifacts_by_run_id is a defaultdict;
        # this lookup will create the entry if missing
        artifact = self._artifacts_by_run_id[run_id].get(name)

        if artifact is not None:
            logger.debug(
                "Found %s with id %s for run %s",
                "output artifact" if name is None else f"artifact '{name}'",
                artifact.id,
                run_id,
            )

            return artifact

        artifact, payloads = make_artifact(value, type_)
        api_client.store_payloads(payloads)

        logger.debug(
            "Created %s with id %s for run %s",
            "output artifact" if name is None else f"artifact '{name}'",
            artifact.id,
            run_id,
        )

        self._artifacts_by_run_id[run_id][name] = artifact
        self._add_artifact(artifact)

        return artifact

    def _populate_graph_from_objects(
        self,
        runs: List[Run],
        artifacts: List[Artifact],
        edges: List[Edge],
    ):
        """Update the in-memory caches of the graph objects using the provided objects."""
        for edge in edges:
            self._add_edge(edge)
        self._runs = {run.id: run for run in runs}
        self._artifacts = {artifact.id: artifact for artifact in artifacts}

    def _populate_graph_from_future(self, future: AbstractFuture) -> Run:
        """
        Update the graph to include the given Future.
        """
        if future.id not in self._runs:
            run = self._make_run(future)
            self._add_run(run)

        # Updating input edges
        for name, value in future.kwargs.items():
            # Updating the input artifact
            artifact_id = None

            maybe_concrete_value = future.resolved_kwargs.get(name, value)
            if not isinstance(maybe_concrete_value, AbstractFuture):
                artifact = self._make_artifact(
                    run_id=future.id,
                    value=maybe_concrete_value,
                    type_=future.function.input_types[name],
                    name=name,
                )

                artifact_id = artifact.id

            # If the input is a future, we connect the edge
            source_run_id = None
            if isinstance(value, AbstractFuture):
                source_run_id = value.id

            # Attempt to link edges across nested graphs
            parent_id = None

            if future.parent_future is not None:
                for (
                    parent_name,
                    parent_value,
                ) in future.parent_future.resolved_kwargs.items():
                    parent_edge = self._get_input_edge(
                        destination_run_id=future.parent_future.id,
                        destination_name=parent_name,
                    )
                    if parent_edge is None:
                        raise RuntimeError("Missing parent edge")

                    if value is parent_value:
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
        if future.state == FutureState.RESOLVED:
            output_artifact = self._make_artifact(
                run_id=future.id,
                value=future.value,
                type_=future.function.output_type,
                name=None,
            )
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
                self._populate_graph_from_future(value)

        return self._runs[future.id]

    def _save_graph(self, runs_only: bool = False, retry: bool = True):
        """
        Persist the graph to the DB.

        Parameters
        ----------
        runs_only:
            If true, only runs will be persisted. Artifacts and edges
            will remain buffered. Should be set to True if the graph is
            being saved only to move the runs to a terminal state, as
            saving only the runs reduces the chances that the entire
            save fails.
        retry:
            Whether the graph saved will be retried. Should be set to
            False when _save_graph is called for cleanup operations so we can
            exit quickly and cleanly.
        """
        runs = list(self._buffer_runs.values())

        if runs_only:
            artifacts = []
            edges = []
        else:
            artifacts = list(self._buffer_artifacts.values())
            edges = list(self._buffer_edges.values())

        if not any(len(buffer) for buffer in (runs, artifacts, edges)):  # type: ignore
            return

        api_client.save_graph(
            root_id=self._futures[0].id,
            runs=runs,
            artifacts=artifacts,
            edges=edges,
            retry=retry,
        )

        self._buffer_runs.clear()

        if not runs_only:
            self._buffer_artifacts.clear()
            self._buffer_edges.clear()

    @classmethod
    def _get_resource_manager(cls) -> ServerResourceManager:
        # lazy init because ServerResourceManager may call the API on init
        if cls._resource_manager is None:
            cls._resource_manager = ServerResourceManager()
        return cls._resource_manager


def make_edge_key(edge: Edge) -> str:
    return "{}:{}:{}:{}".format(
        edge.source_run_id,
        edge.parent_id,
        edge.destination_run_id,
        edge.destination_name,
    )


class RunnerRestartError(RuntimeError):
    pass
