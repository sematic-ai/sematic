# Standard Library
import datetime
import logging
import uuid
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Union

# Third-party
import socketio  # type: ignore

# Sematic
import sematic.api_client as api_client
from sematic.abstract_calculator import CalculatorError
from sematic.abstract_future import AbstractFuture, FutureState
from sematic.caching import (
    CacheNamespace,
    get_future_cache_key,
    resolve_cache_namespace,
)
from sematic.config.config import get_config
from sematic.config.user_settings import get_active_user_settings_strings
from sematic.db.models.artifact import Artifact
from sematic.db.models.edge import Edge
from sematic.db.models.factories import make_artifact, make_run_from_future
from sematic.db.models.resolution import Resolution, ResolutionKind, ResolutionStatus
from sematic.db.models.run import Run
from sematic.graph import Graph
from sematic.resolvers.resource_managers.server_manager import ServerResourceManager
from sematic.resolvers.silent_resolver import SilentResolver
from sematic.utils.exceptions import ExceptionMetadata, format_exception_for_run
from sematic.utils.git import get_git_info
from sematic.utils.retry import retry_call
from sematic.versions import CURRENT_VERSION_STR

logger = logging.getLogger(__name__)


class LocalResolver(SilentResolver):
    """
    A `Resolver` that resolves a pipeline locally.

    Each `Future`'s `Resolution` is tracked in the DB as a run. Each individual function's
    input argument and output value is tracked as an `Artifact`.

    Parameters
    ----------
    cache_namespace: CacheNamespace
        A string or a `Callable` which takes a root `Future` and returns a string, which
        will be used as the cache key namespace in which the executed funcs' outputs will
        be cached, as long as they also have the `cache` flag activated. Defaults to
        `None`.

        The `Callable` option takes as input the `Resolution` root `Future`. All the other
        required variables must be enclosed in the `Callables`' context. The `Callable`
        must have a small memory footprint and must return immediately!
    rerun_from: Optional[str]
        When `None`, the pipeline is resolved from scratch, as normally. When not `None`,
        must be the id of a `Run` from a previous resolution. Instead of running from
        scratch, parts of that previous resolution is cloned up until the specified `Run`,
        and only the specified `Run`, nested and downstream `Future`s are executed. This
        is meant to be used for retries or for hotfixes, without needing to re-run the
        entire pipeline again.
    """

    _resource_manager: Optional[ServerResourceManager] = None  # type: ignore

    def __init__(
        self,
        cache_namespace: Optional[CacheNamespace] = None,
        rerun_from: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self._edges: Dict[str, Edge] = {}
        self._runs: Dict[str, Run] = {}
        self._artifacts: Dict[str, Artifact] = {}

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

        # this parameter needs to be resolved after the root future is enqueued
        # and before the resolution is created
        self._cache_namespace_str: Optional[str] = None
        self._raw_cache_namespace = cache_namespace

    def _seed_graph(self, future: AbstractFuture):
        if self._rerun_from_run_id is None:
            super()._seed_graph(future)
        else:
            self._seed_from_clone(future, self._rerun_from_run_id)

    def _seed_from_clone(self, future: AbstractFuture, from_run_id: str):
        """
        Instead of simply queuing the root future, this method seeds the future graph
        from a clone of another execution of same pipeline.
        """
        try:
            run = api_client.get_run(from_run_id)
        except api_client.ResourceNotFoundError as e:
            raise ValueError(
                f"Cannot restart from {from_run_id}: run cannot be found."
            ) from e

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

        cloned_graph = graph.clone_futures(
            reset_from=from_run_id,
        )

        # Making sure we honor id of future passed from the outside
        cloned_graph.set_root_future_id(future.id)

        self._futures = list(cloned_graph.futures_by_original_id.values())

        # This is necessary, otherwise the root run will not be updated with its
        # cloned status. In detached execution, or rerun, the root run is
        # created outside the resolver (either by the server, or by the resolver
        # submitting the detached resolution from the user's machine).
        self._runs.clear()

        for future in self._futures:
            future.resolved_kwargs = self._get_resolved_kwargs(future)

            if future.state == FutureState.RESOLVED:
                self._artifacts_by_run_id[future.id][
                    None
                ] = cloned_graph.output_artifacts[future.id]

            if future.state in {FutureState.RESOLVED, FutureState.RAN}:
                for name, artifact in cloned_graph.input_artifacts[future.id].items():
                    self._artifacts_by_run_id[future.id][name] = artifact

            self._populate_graph(future)

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
            raise RuntimeError("Not all input arguments are resolved")

        run = self._populate_graph(future)

        return run

    def _connect_to_sio_server(self):
        try:
            retry_call(
                f=self._sio_client.connect,
                fargs=[get_config().socket_io_url],
                fkwargs=dict(namespaces=["/pipeline"]),
                tries=4,
            )
        except BaseException as e:
            # provide the user with useful information, and then continue failing
            logger.error("Could not connect to the socket.io server: %s", e)
            raise

    def _disconnect_from_sio_server(self):
        try:
            retry_call(f=self._sio_client.disconnect, tries=4)
        except BaseException as e:
            # we are shutting down already, so just warn and continue
            logger.warning(
                "Could not cleanly disconnect from the socket.io server: %s", e
            )

    def _resolution_will_start(self) -> None:
        self._connect_to_sio_server()

        @self._sio_client.on("cancel", namespace="/pipeline")
        def _cancel(data):
            if data["resolution_id"] != self._root_future.id:
                return

            logger.warning("Received cancelation event")

            root_run = self._get_run(self._root_future.id)
            if root_run.future_state != FutureState.CANCELED.value:
                raise RuntimeError("Cancelation was not effective.")

            # If we are here, the cancelation was applied successfully server-side
            # so it is safe to mark non-terminal futures as CANCELED
            # This will precipitate the termination of the resolution loop.
            self._clean_up_resolution(save_graph=False)

        self._populate_run_and_artifacts(self._root_future)
        self._save_graph()
        self._cache_namespace_str = self._make_cache_namespace()
        self._create_resolution(self._root_future)
        self._update_resolution_status(ResolutionStatus.RUNNING)

    def _clean_up_resolution(self, save_graph: bool) -> None:
        self._cancel_non_terminal_futures()
        self._deactivate_all_resources()
        self._disconnect_from_sio_server()
        if save_graph:
            self._save_graph()

    def _make_cache_namespace(self) -> Optional[str]:
        """
        Attempts to produce a string cache namespace for the Resolution.

        If the user-supplied cache namespace parameter is:
          - None - returns None
          - a string - returns this string
          - a Callable - invokes it and returns the resulting string

        Must be called after the root future is enqueued, and before the Resolution is
        created.

        Returns
        -------
        A string cache namespace, or None.
        """
        if self._raw_cache_namespace is None:
            logger.debug("The Resolution is not configured to use cached values")
            return None

        try:
            cache_namespace = resolve_cache_namespace(
                cache_namespace=self._raw_cache_namespace,
                root_future=self._root_future,
            )

            logger.info(
                "The Resolution will use the cache namespace: %s", cache_namespace
            )

            return cache_namespace

        except Exception:
            logger.warning(
                "The Resolution is unable to use cached values! "
                "Falling back to execution for all funcs!",
                exc_info=1,  # type: ignore
            )
            return None

    def _resolution_did_cancel(self) -> None:
        super()._resolution_did_cancel()
        api_client.cancel_resolution(self._root_future.id)
        self._clean_up_resolution(save_graph=True)

    def _get_tagged_image(self, tag: str) -> Optional[str]:
        return None

    def _create_resolution(self, root_future):
        """Make a Resolution instance and persist it."""
        resolution = self._make_resolution(root_future)
        api_client.save_resolution(resolution)
        self._notify_pipeline_update()

    def _make_resolution(self, root_future: AbstractFuture) -> Resolution:
        """Make a Resolution instance."""
        resolution = Resolution(
            root_id=root_future.id,
            status=ResolutionStatus.SCHEDULED,
            kind=ResolutionKind.LOCAL,
            git_info=get_git_info(root_future.calculator.func),  # type: ignore
            settings_env_vars=get_active_user_settings_strings(),
            client_version=CURRENT_VERSION_STR,
            cache_namespace=self._cache_namespace_str,
            # the user_id is overwritten on the API call based on the user's API key
            user_id=None,
        )

        return resolution

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

    def _execute_future(self, future: AbstractFuture) -> None:
        """
        Attempts to execute the given Future.

        If the wrapped func is configured for caching, this function attempts to look up
        an Artifact in the cache for the Run, and directly resolves the Future given that
        value, without actually executing it.
        """
        run = self._get_run(future.id)
        # we are certain all input args have been resolved and can compute the cache key
        run.cache_key = self._get_cache_key(future=future)

        if run.cache_key is None:
            super()._execute_future(future=future)
            return

        # attempt to directly resolve the run based on previous executions:
        try:
            run_results = api_client.get_runs(
                limit=1,  # get the original run
                order="asc",  # it's the oldest
                cache_key=run.cache_key,  # must hit the cache key
                future_state="RESOLVED",  # only resolved runs have associated artifacts
            )

            if len(run_results) == 0:
                logger.debug("Cache key %s did not hit any artifact", run.cache_key)
                super()._execute_future(future=future)
                return

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
                future.calculator,
                exc_info=1,  # type: ignore
            )

            super()._execute_future(future=future)
            return

        logger.debug(
            "Cache key %s hit run %s with output artifact %s",
            run.cache_key,
            original_run.id,
            original_artifact.id,
        )
        logger.info(
            "Future %s %s will be resolved from a cached value",
            future.id,
            future.calculator,
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
        #  the run lifecycle should be the main flow the resolver deals with, and the
        #  graph should be a consequence of this, without being updated through lateral
        #  effect such as the run is now, and without this disjointed partial save
        run.original_run_id = original_run.id
        self._add_run(run)
        self._save_graph()

        value = api_client.get_artifact_value(artifact=original_artifact)
        self._update_future_with_value(future=future, value=value)

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

        self._populate_graph(future.nested_future)
        self._add_run(run)
        self._save_graph()

    def _future_did_resolve(self, future: AbstractFuture) -> None:
        super()._future_did_resolve(future)

        run = self._get_run(future.id)
        run.future_state = FutureState.RESOLVED
        run.resolved_at = datetime.datetime.utcnow()

        self._populate_graph(future)
        self._add_run(run)
        self._save_graph()

    def _future_did_get_marked_for_retry(self, future: AbstractFuture) -> None:
        super()._future_did_get_marked_for_retry(future)

        run = self._get_run(future.id)

        run.future_state = FutureState.RETRYING

        self._add_run(run)
        self._save_graph()

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
        self._save_graph()

    def _notify_pipeline_update(self):
        api_client.notify_pipeline_update(
            self._runs[self._root_future.id].calculator_path
        )

    def _resolution_did_succeed(self) -> None:
        super()._resolution_did_succeed()
        self._update_resolution_status(ResolutionStatus.COMPLETE)
        self._notify_pipeline_update()
        self._disconnect_from_sio_server()

    def _resolution_did_fail(self, error: Exception) -> None:
        super()._resolution_did_fail(error)
        if isinstance(error, CalculatorError):
            reason = "Marked as failed because another run in the graph failed."
            resolution_status = ResolutionStatus.COMPLETE
        elif isinstance(error, _ResolverRestartError):
            reason = "Marked as failed because the resolver restarted mid-execution."
            resolution_status = ResolutionStatus.FAILED
        else:
            reason = "Marked as failed because the rest of the graph failed to resolve."
            resolution_status = ResolutionStatus.FAILED

        self._move_runs_to_terminal_state(reason, fail_root_run=True)
        self._update_resolution_status(resolution_status)
        self._disconnect_from_sio_server()
        self._notify_pipeline_update()

    def _move_runs_to_terminal_state(self, reason, fail_root_run: bool):
        for run_id in self._runs.keys():
            run = self._get_run(run_id)  # may have terminated remotely, re-get from api
            state = FutureState.as_object(run.future_state)

            if state.is_terminal():
                continue

            if run.parent_id is None and fail_root_run:
                # If the resolution failed due to an error in the resolver
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

        self._save_graph()

    def _update_resolution_status(self, status: ResolutionStatus):
        resolution = api_client.get_resolution(self._root_future.id)
        current_status = ResolutionStatus[resolution.status]  # type: ignore
        if (
            status == ResolutionStatus.RUNNING
            and current_status != ResolutionStatus.SCHEDULED
        ):
            raise _ResolverRestartError(
                "It appears that the resolver has restarted mid-execution. "
                "The cluster may be under pressure."
            )
        resolution.status = status
        api_client.save_resolution(resolution)

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

        logger.debug("Created run %s for %s", run.id, future.calculator)
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
                future.calculator,
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
                future.calculator,
                exc_info=1,  # type: ignore
            )
            return None

        logger.debug(
            "Future %s %s will use the cache key: %s",
            future.id,
            future.calculator,
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

    def _populate_graph(self, future: AbstractFuture) -> Run:
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

            maybe_resolved_value = future.resolved_kwargs.get(name, value)
            if not isinstance(maybe_resolved_value, AbstractFuture):
                artifact = self._make_artifact(
                    run_id=future.id,
                    value=maybe_resolved_value,
                    type_=future.calculator.input_types[name],
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
                type_=future.calculator.output_type,
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


class _ResolverRestartError(RuntimeError):
    pass
