# Standard Library
import datetime
import logging
import time
from typing import Any, Dict, List, Optional

# Third-party
import cloudpickle

# Sematic
import sematic.api_client as api_client
from sematic.abstract_future import AbstractFuture, FutureState, clone_future
from sematic.container_images import (
    DEFAULT_BASE_IMAGE_TAG,
    MissingContainerImage,
    get_image_uris,
)
from sematic.db.models.artifact import Artifact
from sematic.db.models.edge import Edge
from sematic.db.models.resolution import PipelineRunKind, PipelineRunStatus
from sematic.db.models.run import Run
from sematic.graph import RerunMode
from sematic.plugins.abstract_external_resource import AbstractExternalResource
from sematic.runners.local_runner import LocalRunner, RunnerRestartError, make_edge_key
from sematic.utils.exceptions import format_exception_for_run
from sematic.utils.memoized_property import memoized_property

logger = logging.getLogger(__name__)


_MAX_DELAY_BETWEEN_STATUS_UPDATES_SECONDS = 60  # 60s => 1 min
_DELAY_BETWEEN_STATUS_UPDATES_BACKOFF = 1.25

# It is important not to change these! They are used for identifying the start/end of
# inline run logs. If you change it, inline logs written with prior versions of Sematic
# might not be readable for new versions of Sematic.
START_INLINE_RUN_INDICATOR = "--------- Sematic Start Inline Run {} ---------"
END_INLINE_RUN_INDICATOR = "--------- Sematic End Inline Run {} ---------"


class CloudRunner(LocalRunner):
    """
    Runs a pipeline on a Kubernetes cluster.

    Parameters
    ----------
    detach: bool
        Defaults to `True`.

        When `True`, the driver job will run on the remote cluster. This is the
        so called `fire-and-forget` mode. The shell prompt will return as soon
        as the driver job as been submitted.

        When `False`, the driver job runs on the local machine. The shell prompt
        will return when the entire pipeline has completed.
    cache_namespace: CacheNamespace
        A string or a `Callable` which takes a root `Future` and returns a
        string, which will be used as the cache key namespace in which the
        executed funcs' outputs will be cached, as long as they also have the
        `cache` flag activated. Defaults to `None`.

        The `Callable` option takes as input the `PipelineRun` root `Future`. All
        the other required variables must be enclosed in the `Callables`'
        context. The `Callable` must have a small memory footprint and must
        return immediately!
    max_parallelism: Optional[int]
        The maximum number of Standalone Function Runs that this runner will
        allow to be in the `SCHEDULED` state at any one time. Must be a positive
        integer, or `None` for unlimited runs. Defaults to `None`. This is
        intended as a simple mechanism to limit the amount of computing
        resources consumed by one pipeline execution for pipelines with a high
        degree of parallelism. Note that if other runners are active, runs
        from them will not be considered in this parallelism limit. Note also
        that runs that are in the RAN state do not contribute to the limit,
        since they do not consume computing resources.
    rerun_from: Optional[str]
        When `None`, the pipeline is executed from scratch, as normally. When
        not `None`, must be the id of a `Run` from a previous pipeline run.
        Instead of running from scratch, parts of that previous pipeline run is
        cloned up until the specified `Run`, and only the specified `Run`,
        nested and downstream `Future`s are executed. This is meant to be used
        for retries or for hotfixes, without needing to re-run the entire
        pipeline again.
    _is_running_remotely: bool
        For Sematic internal usage. End users should always leave this at the
        default value of `False`.
    """

    # Time between external resource updates *during activation and deactivation*
    _RESOURCE_UPDATE_INTERVAL_SECONDS = 10

    # Time that external resources have to activate before
    # hitting a timeout.
    _RESOURCE_ACTIVATION_TIMEOUT_SECONDS = 30 * 60  # 30 min

    def __init__(
        self,
        detach: bool = True,
        max_parallelism: Optional[int] = None,
        _is_running_remotely: bool = False,
        _base_image_tag: str = "default",
        **kwargs,
    ):
        super().__init__(**kwargs)

        # detach:
        #   True: default, the user wants to submit a detached pipeline run
        #   False: the user wants to keep pipeline run attached, i.e. running on
        #           their machine
        self._detach = detach

        self._pipeline_run_was_created = _is_running_remotely

        # _is_running_remotely:
        #   True: we are running in a remote driver job
        #   False: default we are running on a local user machine
        self._is_running_remotely = _is_running_remotely

        if max_parallelism is not None and max_parallelism < 1:
            raise ValueError(
                "max_parallelism must be a positive integer or None. "
                f"Got: {max_parallelism}"
            )
        self._max_parallelism = max_parallelism

        # When multiple base images are specified through the build info (Bazel target)
        # this is the tag we use to find the pipeline run image
        self._base_image_tag = _base_image_tag or DEFAULT_BASE_IMAGE_TAG

    def run(self, future: AbstractFuture) -> Any:
        if not self._detach:
            return super().run(future)

        with self._catch_pipeline_run_errors():
            self._enqueue_root_future(future)
            return self._detach_pipeline_run(future)

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

    @memoized_property
    def _container_image_uris(self) -> Optional[Dict[str, str]]:
        # If we are launching a detached execution, we can get the image URIs
        # from the environment/build. We then put them in the pipeline run we
        # create. However, if we are *executing* a detached
        # execution, the environment doesn't contain the image URIs. So we will
        # need to get the image URIs frm the pipeline run we put them in earlier.
        if self._is_running_remotely:
            pipeline_run = api_client.get_pipeline_run(self._root_future.id)
            uri_mapping = pipeline_run.container_image_uris
            if uri_mapping is None:
                # probably shouldn't happen: the only pipeline runs without this
                # should be from old runs. But this makes mypy happy and is a
                # good sanity check
                raise RuntimeError(
                    "Pipeline Run does not have mapping for custom base images"
                )
            return uri_mapping
        else:
            return get_image_uris()

    def _get_container_image(self, future: AbstractFuture) -> Optional[str]:
        if self._container_image_uris is None:
            return None

        if not future.props.standalone:
            return self._get_pipeline_run_container_image()

        base_image_tag = future.props.base_image_tag or DEFAULT_BASE_IMAGE_TAG

        return self._get_tagged_image(base_image_tag)

    def _get_pipeline_run_container_image(self) -> Optional[str]:
        if not self._detach:
            return None

        return self._get_tagged_image(self._base_image_tag)

    def _get_tagged_image(self, tag: str) -> Optional[str]:
        if self._container_image_uris is None:
            return None

        try:
            return self._container_image_uris[tag]
        except KeyError:
            raise MissingContainerImage(f"{tag} was not built.")

    def _create_pipeline_run(self, root_future):
        if self._is_running_remotely:
            # pipeline run should have been created prior to the runner
            # actually starting its remote execution.
            return

        return super()._create_pipeline_run(root_future)

    def _make_pipeline_run(self, root_future):
        pipeline_run = super()._make_pipeline_run(root_future)

        # Mapping for the rest of the runs in the graph
        pipeline_run.container_image_uris = self._container_image_uris
        # Image for the pipeline run itself
        pipeline_run.container_image_uri = self._get_pipeline_run_container_image()

        if self._detach:
            pipeline_run.status = PipelineRunStatus.CREATED
            pipeline_run.kind = PipelineRunKind.KUBERNETES

        return pipeline_run

    def _make_run(self, future: AbstractFuture) -> Run:
        run = super()._make_run(future)
        run.container_image_uri = self._get_container_image(future)
        return run

    def _update_run_and_future_pre_scheduling(self, run: Run, future: AbstractFuture):
        # For the cloud runner, the server will update the relevant
        # run fields when it gets scheduled by the server.
        # Inline futures still need the updates.
        if future.props.standalone:
            return

        super()._update_run_and_future_pre_scheduling(run, future)

    def _detach_pipeline_run(self, future: AbstractFuture) -> str:
        run = self._populate_run_and_artifacts(future)
        self._save_graph()
        self._cache_namespace_str = self._make_cache_namespace()
        self._create_pipeline_run(future)
        run.root_id = future.id

        api_client.notify_pipeline_update(run.function_path)

        # SUBMIT RUNNER JOB
        api_client.schedule_pipeline_run(
            pipeline_run_id=future.id,
            max_parallelism=self._max_parallelism,
            rerun_from=self._rerun_from_run_id,
            rerun_mode=self._rerun_mode,
        )

        return run.id

    def _schedule_future(self, future: AbstractFuture) -> None:
        pre_query_run_summary = str(self._runs)
        run = self._get_run(future.id)
        if run.future_state not in (
            FutureState.CREATED.value,
            FutureState.RETRYING.value,
        ):
            # It's unclear how we wind up in this situation, but it shouldn't be fatal.
            # Log some info to help diagnose, and move on.
            logger.warning(
                "Tried to double schedule %s. Futures: %s. "
                "Runs (before query): %s. Buffer runs: %s. Retrieved run: %s",
                run.id,
                self._futures,
                pre_query_run_summary,
                self._buffer_runs,
                run,
            )
        else:
            try:
                run = api_client.schedule_run(future.id)
                logger.info("Scheduled run: %s", run)
            except Exception:
                logger.error(
                    "Error scheduling run %s. Futures: %s. "
                    "Runs: %s. Buffer runs: %s. Retrieved run: %s",
                    run.id,
                    self._futures,
                    self._runs,
                    self._buffer_runs,
                    run,
                )
                raise

        # Why not self._add_run()? Because the relevant change is already
        # in the DB. And adding it to save again might make it so we overwrite
        # changes to the run made by the run job itself as it executes.
        self._runs[run.id] = run
        self._set_future_state(future, FutureState[run.future_state])  # type: ignore

    def _wait_for_scheduled_runs(self) -> None:
        run_ids = self._wait_for_any_inline_runs() or self._wait_for_any_remote_jobs()

        for run_id in run_ids:
            self._process_run_output(run_id)

    def _process_run_output(self, run_id: str) -> None:
        self._refresh_graph(run_id)

        run = self._get_run(run_id)

        future = next(future for future in self._futures if future.id == run.id)

        # if the external run is reported to not have completed successfully by the server
        if run.future_state not in {FutureState.RESOLVED.value, FutureState.RAN.value}:
            self._handle_future_failure(
                future, run.exception_metadata, run.external_exception_metadata
            )
            return

        if run.nested_future_id is not None:
            pickled_nested_future = api_client.get_future_bytes(run.nested_future_id)
            value = cloudpickle.loads(pickled_nested_future)

        else:
            output_edge = self._get_output_edges(run.id)[0]

            # Pleasing mymy
            if output_edge.artifact_id is None:
                raise RuntimeError("Missing output artifact")

            output_artifact = self._artifacts[output_edge.artifact_id]
            self._artifacts_by_run_id[run.id][None] = output_artifact
            value = api_client.get_artifact_value(output_artifact)

        self._update_future_with_value(future, value)

    def _pipeline_run_did_fail(
        self, error: Exception, reason: Optional[str] = None
    ) -> None:
        if not isinstance(error, RunnerRestartError):
            super()._pipeline_run_did_fail(error)
            return

        try:
            new_root_future = clone_future(self._root_future)
            new_runner = self.__class__(
                cache_namespace=self._cache_namespace_str,
                rerun_from=self._root_future.id,
                rerun_mode=RerunMode.CONTINUE,
                detach=True,
                max_parallelism=self._max_parallelism,
                _base_image_tag=self._base_image_tag,
            )
            new_runner._git_info = api_client.get_pipeline_run(
                self._root_future.id
            ).git_info
            new_runner.run(new_root_future)
            reason = (
                f"Pipeline Run restarted mid-execution. A new one has been started "
                f"with the id {new_root_future.id}"
            )
            logger.error(reason)
        finally:
            super()._pipeline_run_did_fail(error, reason)

    def _future_did_fail(self, failed_future: AbstractFuture) -> None:
        # Unlike LocalRunner._future_did_fail, we only care about
        # failing parent futures since runs are marked FAILED by worker.py
        run = self._get_run(failed_future.id)
        if (
            failed_future.state == FutureState.FAILED
            and run is not None
            and run.exception_metadata is None
        ):
            run.exception_metadata = format_exception_for_run()

        run.future_state = failed_future.state
        run.failed_at = datetime.datetime.utcnow()

        self._add_run(run)
        self._save_graph()

        if failed_future.state == FutureState.NESTED_FAILED:
            super()._future_did_fail(failed_future)

    def _refresh_graph(self, run_id: str) -> None:
        """
        Refresh graph for run ID.

        Will only refresh artifacts and edges directly connected to run.
        """
        runs, artifacts, edges = api_client.get_graph(run_id)

        for run in runs:
            self._runs[run.id] = run

        for artifact in artifacts:
            self._artifacts[artifact.id] = artifact

        for edge in edges:
            self._edges[make_edge_key(edge)] = edge

    def _wait_for_any_inline_runs(self) -> List[str]:
        return [
            future.id
            for future in self._futures
            if not future.props.standalone and future.state == FutureState.SCHEDULED
        ]

    def _wait_for_any_remote_jobs(self) -> List[str]:
        scheduled_futures_by_id: Dict[str, AbstractFuture] = {
            future.id: future
            for future in self._futures
            if future.props.standalone and future.state == FutureState.SCHEDULED
        }

        if not scheduled_futures_by_id:
            logger.info("No futures to wait on")
            return []

        delay_between_updates = 1.0
        while True:
            updated_states: Dict[
                str, FutureState
            ] = api_client.update_run_future_states(
                list(scheduled_futures_by_id.keys())
            )
            logger.info(
                "Checking for updates on run ids: %s",
                list(scheduled_futures_by_id.keys()),
            )
            changed_job_ids = []
            for run_id, new_state in updated_states.items():
                future = scheduled_futures_by_id[run_id]
                if new_state != FutureState.SCHEDULED:
                    # no need to actually update the future's state here, that will
                    # be handled by the post-processing logic once it is aware this
                    # future has changed
                    self._refresh_graph(future.id)
                    changed_job_ids.append(future.id)

            if changed_job_ids:
                return changed_job_ids

            logger.info("Sleeping for %ss", delay_between_updates)
            time.sleep(delay_between_updates)
            delay_between_updates = min(
                _MAX_DELAY_BETWEEN_STATUS_UPDATES_SECONDS,
                _DELAY_BETWEEN_STATUS_UPDATES_BACKOFF * delay_between_updates,
            )

    def _start_inline_execution(self, future_id) -> None:
        """Callback called before an inline execution."""
        logger.info(START_INLINE_RUN_INDICATOR.format(future_id))

    def _end_inline_execution(self, future_id) -> None:
        """Callback called at the end of an inline execution."""
        logger.info(END_INLINE_RUN_INDICATOR.format(future_id))

    def _can_schedule_future(self, future: AbstractFuture) -> bool:
        """Returns whether the specified future can be scheduled.

        Inline futures can always be scheduled. External futures can only be scheduled
        if the maximum parallelism degree has not been exceeded.
        """
        if not future.props.standalone:
            return True

        if not self._max_parallelism:
            return True

        remote_runs = self._get_remote_runs_count()
        logging.debug(
            "Have %s remote runs scheduled out of a maximum of %s",
            remote_runs,
            self._max_parallelism,
        )
        return remote_runs < self._max_parallelism

    def _get_remote_runs_count(self) -> int:
        """Returns the known number of futures in the SCHEDULED state."""
        return sum(map(lambda f: f.state == FutureState.SCHEDULED, self._futures))

    @classmethod
    def _do_resource_activate(
        cls, resource: AbstractExternalResource
    ) -> AbstractExternalResource:
        resource = api_client.activate_external_resource(resource.id)
        return resource

    @classmethod
    def _do_resource_deactivate(
        cls, resource: AbstractExternalResource
    ) -> AbstractExternalResource:
        resource = api_client.deactivate_external_resource(resource.id)
        return resource

    @classmethod
    def _do_resource_update(
        cls, resource: AbstractExternalResource
    ) -> AbstractExternalResource:
        resource = api_client.get_external_resource(resource.id, refresh_remote=True)
        return resource

    @classmethod
    def entering_resource_context(cls, resource: AbstractExternalResource):
        cls._get_resource_manager().poll_for_updates_by_resource_id(resource.id)

    @classmethod
    def exiting_resource_context(cls, resource_id: str):
        cls._get_resource_manager().stop_poll_for_updates_by_resource_id(resource_id)
