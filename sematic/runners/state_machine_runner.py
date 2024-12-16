"""
Abstract base class for a state machine-based DAG execution.
"""

# Standard Library
import abc
import logging
import math
import os
import signal
import sys
import time
import typing
from contextlib import contextmanager

# Sematic
from sematic.abstract_function import FunctionError
from sematic.abstract_future import AbstractFuture, FutureState, TimeoutFuturePair
from sematic.plugins.abstract_external_resource import (
    AbstractExternalResource,
    ResourceState,
)
from sematic.resolvers.abstract_resource_manager import AbstractResourceManager
from sematic.runner import Runner
from sematic.utils.exceptions import (
    CancellationError,
    ExceptionMetadata,
    ExternalResourceError,
    PipelineRunError,
    TimeoutError,
    format_exception_for_run,
)
from sematic.utils.signals import FrameType, HandlerType, call_signal_handler
from sematic.utils.timeout import timeout


logger = logging.getLogger(__name__)


class StateMachineRunner(Runner, abc.ABC):
    # Time between resource updates *during activation and deactivation*
    _RESOURCE_UPDATE_INTERVAL_SECONDS = 1

    def __init__(self) -> None:
        self._futures: typing.List[AbstractFuture] = []

    @property
    def _root_future(self) -> AbstractFuture:
        if len(self._futures) == 0:
            raise RuntimeError("No root future: no futures were enqueued.")

        return self._futures[0]

    def run(self, future: AbstractFuture) -> typing.Any:
        with self._catch_pipeline_run_errors():
            self._seed_graph(future)
            self._pipeline_run_loop()

        return self._root_future.value

    def _seed_graph(self, future):
        """
        Set the initial futures for the pipeline run.

        This is a stub that can be
        overridden by child classes. The runner will evolve the DAG using this initial
        set of futures. The root future should always be element 0 of `self._futures`,
        there are no requirements on order of other futures. The default implementation
        just seeds with the root future itself and no others.
        """
        self._enqueue_root_future(future)

    def _pipeline_run_loop(self):
        """
        Assuming that the future graph was seeded, this method will proceed
        through the graph until the root future has a known value.
        """
        self._register_signal_handlers()

        logger.info(f"Starting pipeline run {self._root_future.id}")

        self._pipeline_run_will_start()

        while not self._root_future.state.is_terminal():
            state_changed = False
            for future_ in self._futures:
                if future_.state == FutureState.CREATED:
                    state_changed |= self._schedule_future_if_args_concrete(future_)
                    continue
                if future_.state == FutureState.RETRYING:
                    state_changed |= self._execute_future(future_)
                    continue
                if future_.state == FutureState.RAN:
                    state_changed |= self._run_nested_future(future_)
                    continue

                # should be unreachable code, here for a sanity check
                if (
                    future_.state != FutureState.SCHEDULED
                    and not future_.state.is_terminal()
                ):
                    raise RuntimeError(
                        f"Illegal state: future {future_.id} in state {future_.state}"
                        " when it should have been already processed"
                    )

            if not state_changed:
                logger.info("Entering wait")
                # we only want to enter a waiting state if nothing changed.
                # otherwise there might be other things we can schedule
                # before starting the wait.
                self._wait_for_scheduled_runs_with_timeout()
            else:
                logger.info("Checking for ability to schedule more")

        if self._root_future.state == FutureState.RESOLVED:
            self._pipeline_run_did_succeed()
        elif self._root_future.state == FutureState.CANCELED:
            return
        else:
            raise RuntimeError("Future does not have known value after runner call.")

    @contextmanager
    def _catch_pipeline_run_errors(self):
        try:
            yield
        except CancellationError as e:
            logger.warning("Terminating runner loop due to cancellation.")
            self._pipeline_run_did_cancel()
            raise e
        except Exception as e:
            logger.info(
                "Pipeline run %s has failed; starting cleanup; look for details below",
                self._root_future.id,
            )
            try:
                self._pipeline_run_did_fail(error=e)
            except Exception:
                logger.exception("Unable to fail pipeline run:")

            if isinstance(e, FunctionError) and hasattr(e, "__cause__"):
                # this will simplify the stack trace so the user sees less
                # from Sematic's stack and more from the error from their code.
                raise e.__cause__  # type: ignore
            raise e

    def _enqueue_root_future(self, future: AbstractFuture):
        concrete_kwargs = self._get_concrete_kwargs(future)
        if not len(concrete_kwargs) == len(future.kwargs):
            raise ValueError(
                "All input arguments of your root function should be concrete."
            )

        future.resolved_kwargs = concrete_kwargs

        # Cleaning up
        self._futures.clear()

        self._enqueue_future(future)

    def _cancel_on_sigterm(self) -> bool:
        return True

    def _register_signal_handlers(self) -> None:
        runner_pid = os.getpid()
        original_handlers: typing.Dict[int, HandlerType] = dict()

        def _handle_sig_cancel(signum: int, frame: FrameType) -> None:
            if runner_pid == os.getpid():
                if self._cancel_on_sigterm():
                    logger.warning(
                        "Received signal %s; canceling pipeline run...", signum
                    )
                    self._pipeline_run_did_cancel()

                    # Raising an error ensures execution doesn't resume where it left off
                    # after the handler exits.
                    raise CancellationError(
                        f"Pipeline run cancelled due to signal {signum}"
                    )
                else:
                    # Common exit code for exits due to a particular signal
                    # is signal number + 128:
                    # https://stackoverflow.com/a/1535733/2540669
                    exit_code = 128 + signum
                    logger.warning(
                        "Received signal %s; exiting with code %s...", signum, exit_code
                    )
                    sys.stderr.flush()
                    sys.stdout.flush()
                    sys.exit(exit_code)

            # this branch is possible when using LocalRunner,
            # or if inlined funcs spawn processes when using CloudRunner
            else:
                call_signal_handler(original_handlers[signum], signum, frame)

        for signum in {signal.SIGINT, signal.SIGTERM}:
            original_handlers[signum] = signal.signal(  # type: ignore
                signum, _handle_sig_cancel
            )

    def _enqueue_future(self, future: AbstractFuture) -> None:
        if future in self._futures:
            return

        self._futures.append(future)

        for value in future.kwargs.values():
            if isinstance(value, AbstractFuture):
                value.parent_future = future.parent_future
                self._enqueue_future(value)

    def _can_schedule_future(self, _: AbstractFuture) -> bool:
        """Returns whether the specified future can be scheduled."""
        return True

    @abc.abstractmethod
    def _schedule_future(self, future: AbstractFuture) -> None:
        pass

    @abc.abstractmethod
    def _run_inline(self, future: AbstractFuture) -> None:
        pass

    @abc.abstractmethod
    def _wait_for_scheduled_runs(self) -> None:
        pass

    def _fail_future_with_timeout(
        self,
        executing_future: AbstractFuture,
        timeout_restricting_future: typing.Optional[AbstractFuture] = None,
    ):
        if timeout_restricting_future is None:
            timeout_restricting_future = executing_future

        if timeout_restricting_future.id == executing_future.id:
            message = (
                f"The Sematic function {executing_future.function.__name__} did not "
                f"complete in time to satisfy its "
                f"{executing_future.props.timeout_mins} minute timeout."
            )
        else:
            message = (
                f"The Sematic function {executing_future.function.__name__} did not "
                f"complete in time to satisfy the "
                f"{timeout_restricting_future.props.timeout_mins} minute timeout "
                f"specified by its ancestor "
                f"{timeout_restricting_future.function.__name__}."
            )
        self._handle_future_failure(
            executing_future,
            format_exception_for_run(TimeoutError(message)),
        )

    def _wait_for_scheduled_runs_with_timeout(self) -> None:
        seconds_until_next_timeout, future = self._get_seconds_to_next_timeout()
        if seconds_until_next_timeout is not None and future is not None:
            if seconds_until_next_timeout <= 0 and not future.state.is_terminal():
                # a future had already expired before we even started waiting.
                self._fail_future_with_timeout(future)
                return
            logger.info(
                "Next timeout is in %s seconds, for %s",
                seconds_until_next_timeout,
                future.id,
            )

        try:
            with timeout(seconds_until_next_timeout):
                self._wait_for_scheduled_runs()
        except TimeoutError:
            if future is not None and not future.state.is_terminal():
                self._fail_future_with_timeout(future)
            elif future is not None:
                logger.warning(
                    "Received TimeoutError, but %s is already in terminal state %s",
                    future.id,
                    future.state,
                )

    def _get_seconds_to_next_timeout(
        self,
    ) -> TimeoutFuturePair:
        remaining_timeout_future_pairs = [
            (math.ceil(future.props.remaining_timeout_seconds), future)  # type: ignore
            for future in self._futures
            if future.props.remaining_timeout_seconds is not None
        ]
        if len(remaining_timeout_future_pairs) == 0:
            return None, None

        # If there are two futures that timeout at the same time (ex: parallel
        # runs that used the same timeout duration and started simultaneously),
        # we fall back to comparing ids lexically to break the tie (future objects
        # are not comparable, so we use the id).
        return min(remaining_timeout_future_pairs, key=lambda pair: (pair[0], pair[1].id))

    def _cancel_non_terminal_futures(self):
        for future in self._futures:
            state = self._read_refreshed_state(future)
            if state != future.state:
                logger.debug(
                    "In-memory future state '%s' differs from refreshed state"
                    "'%s' during cleanup.",
                    future.state,
                    state,
                )
            if not state.is_terminal():
                self._set_future_state(future, FutureState.CANCELED)

    def _read_refreshed_state(self, future: AbstractFuture) -> FutureState:
        """Refresh state from the 'source of truth.'

        The refreshed state should be returned, but the `state` field of
        `future` should be unmodified.

        For silent runner, the source of truth is in-memory. Runners that
        use a server should refresh the state from there.
        """
        return future.state

    @typing.final
    def _set_future_state(self, future, state):
        # type: (AbstractFuture, FutureState) -> None
        """
        Sets state on future and call corresponding callback.
        """
        future.state = state

        CALLBACKS = {
            FutureState.SCHEDULED: self._future_did_schedule,
            FutureState.RAN: self._future_did_run,
            FutureState.FAILED: self._future_did_fail,
            FutureState.NESTED_FAILED: self._future_did_fail,
            FutureState.CANCELED: self._future_did_cancel,
            FutureState.RESOLVED: self._future_did_resolve,
            FutureState.RETRYING: self._future_did_get_marked_for_retry,
        }

        if state in CALLBACKS:
            CALLBACKS[state](future)

        if state.is_terminal():
            self._future_did_terminate(future)

    # State machine lifecycle hooks

    def _pipeline_run_will_start(self) -> None:
        """
        Callback allowing runners to implement custom actions.

        This is called when `run` has been called and
        before any future get scheduled for execution.
        """
        pass

    def _pipeline_run_did_succeed(self) -> None:
        """
        Callback allowing runners to implement custom actions.

        This is called after the root future's return value is concrete.
        """
        pass

    def _pipeline_run_did_fail(self, error: Exception) -> None:
        """
        Callback allowing runners to implement custom actions.

        This is called after a future has failed and the exception is about to be raised.

        Parameters
        ----------
        error:
            The error that led to the pipeline run's failure. If the error occurred
            within a function, will be an instance of FunctionError
        """
        pass

    def _pipeline_run_did_cancel(self) -> None:
        """
        Callback allowing runners to implement custom actions.

        This is called after a future was canceled.
        """
        pass

    def _future_did_schedule(self, future: AbstractFuture) -> None:
        """
        Callback allowing runners to implement custom actions.

        This is called after a future was scheduled.
        """
        pass

    def _future_did_run(self, future: AbstractFuture) -> None:
        """
        Callback allowing runners to implement custom actions.

        This is called after a future finished running (its value
        may not be concrete).
        """
        pass

    def _future_did_fail(self, failed_future: AbstractFuture) -> None:
        """
        Callback allowing specific runners to react when a future is marked failed.
        """
        pass

    def _future_did_cancel(self, canceled_future: AbstractFuture) -> None:
        """
        Callback allowing specific runners to react when a future is marked canceled.

        Note that if a run was marked cancelled on the server, this callback may not
        be invoked for the corresponding future. It should thus be used primarily for
        ensuring the server state reflects cancellation if the cancellation is detected
        by the runner before the server handles it.
        """
        pass

    def _future_did_terminate(self, failed_future: AbstractFuture) -> None:
        """Callback for runners to react when a future is marked in a terminal state.

        This should be used instead of callbacks like future_did_fail, future_did_run
        if you want to ensure that the callback happens regardless of which terminal state
        the future entered.

        It will be called AFTER the more specific future state callbacks.
        """
        pass

    def _future_did_resolve(self, future: AbstractFuture) -> None:
        """
        Callback allowing specific runners to react when a future is marked resolved.
        """
        pass

    def _future_will_schedule(self, future: AbstractFuture) -> None:
        """
        Callback allowing specific runners to react when a future is about to
        be scheduled.
        """
        pass

    def _future_did_get_marked_for_retry(self, future: AbstractFuture) -> None:
        """
        Callback allowing specific runners to react when a future is about to
        be retried.
        """
        pass

    @staticmethod
    def _get_concrete_kwargs(future: AbstractFuture) -> typing.Dict[str, typing.Any]:
        """
        Extract only concrete kwargs.
        """
        concrete_kwargs = {}
        for name, value in future.kwargs.items():
            if isinstance(value, AbstractFuture):
                if value.state == FutureState.RESOLVED:
                    concrete_kwargs[name] = value.value
            else:
                concrete_kwargs[name] = value

        return concrete_kwargs

    @typing.final
    def _schedule_future_if_args_concrete(self, future: AbstractFuture) -> bool:
        """Schedule a future if its inputs are ready. Return True if it was scheduled."""
        concrete_kwargs = self._get_concrete_kwargs(future)

        all_args_concrete = len(concrete_kwargs) == len(future.kwargs)

        if all_args_concrete:
            future.resolved_kwargs = concrete_kwargs
            return self._execute_future(future)
        return False

    def _execute_future(self, future: AbstractFuture) -> bool:
        """
        Attempts to execute the given Future. Returns true if it did.
        """
        if not self._can_schedule_future(future):
            logger.info("Currently not scheduling %s", future.function)
            return False

        self._future_will_schedule(future)

        if future.props.standalone:
            logger.info("Scheduling %s %s", future.id, future.function)
            self._schedule_future(future)
            return True
        else:
            logger.info("Running inline %s %s", future.id, future.function)
            self._run_inline(future)
            return True

    @typing.final
    def _run_nested_future(self, future: AbstractFuture) -> bool:
        """Bubble resolved state up the tree. Return true if a state was changed"""
        if future.nested_future is None:
            raise RuntimeError("No nested future")

        nested_future = future.nested_future
        nested_future.parent_future = future
        if nested_future.state == FutureState.RESOLVED:
            future.value = nested_future.value
            self._set_future_state(future, FutureState.RESOLVED)
            return True
        return False

    def _handle_future_failure(
        self,
        future: AbstractFuture,
        exception_metadata: typing.Optional[ExceptionMetadata] = None,
        external_exception_metadata: typing.Optional[ExceptionMetadata] = None,
    ) -> None:
        """
        When a future fails, its state machine as well as that of its parent
        futures need to be updated.

        Parameters
        ----------
        exception_metadata:
            Metadata describing an exception which occurred during code execution
            (Pipeline, Runner, Driver)
        external_exception_metadata:
            Metadata describing an exception which occurred in external compute
            infrastructure
        """
        retry_settings = future.props.retry_settings

        if retry_settings is None:
            logging.info(f"No retries configured for {future.id}, failing now.")
            self._fail_future_and_parents(future)
            raise PipelineRunError(exception_metadata, external_exception_metadata)

        if not retry_settings.should_retry(
            exception_metadata, external_exception_metadata
        ):
            logging.info(
                "Retries exhausted or exception not retriable for "
                f"{future.id}, failing now."
            )
            self._fail_future_and_parents(future)
            raise PipelineRunError(exception_metadata, external_exception_metadata)

        retries_left = retry_settings.retries - retry_settings.retry_count
        logger.info(f"Retrying {future.id}. {retries_left} retries left.")
        self._set_future_state(future, FutureState.RETRYING)
        retry_settings.retry_count += 1

    def _fail_future_and_parents(self, future: AbstractFuture) -> None:
        """
        Mark the future FAILED and its parent futures NESTED_FAILED.
        """
        self._set_future_state(future, FutureState.FAILED)

        parent_future = future.parent_future
        while parent_future is not None:
            self._set_future_state(parent_future, FutureState.NESTED_FAILED)
            parent_future = parent_future.parent_future

    def _update_future_with_value(
        self, future: AbstractFuture, value: typing.Any
    ) -> None:
        try:
            value = future.function.cast_output(value)
        except TypeError as e:
            logger.error("Unable to process future value", exc_info=e)
            self._handle_future_failure(future, format_exception_for_run(e))
            return

        if isinstance(value, AbstractFuture):
            self._set_nested_future(future, value)
            self._set_future_state(future, FutureState.RAN)
        else:
            future.value = value
            self._set_future_state(future, FutureState.RESOLVED)

    def _set_nested_future(
        self, future: AbstractFuture, nested_future: AbstractFuture
    ) -> None:
        """
        Setting a nested future on a RAN future.
        """
        future.nested_future = nested_future
        nested_future.parent_future = future
        self._enqueue_future(nested_future)

    @classmethod
    def classpath(cls) -> str:
        return f"{cls.__module__}.{cls.__name__}"

    @classmethod
    def _get_resource_manager(cls) -> AbstractResourceManager:
        raise NotImplementedError("Child classes must implement _get_resource_manager")

    @classmethod
    def _do_resource_activate(
        cls, resource: AbstractExternalResource
    ) -> AbstractExternalResource:
        raise NotImplementedError("Child classes must implement _do_resource_activate")

    @classmethod
    def _do_resource_deactivate(
        cls, resource: AbstractExternalResource
    ) -> AbstractExternalResource:
        raise NotImplementedError("Child classes must implement _do_resource_deactivate")

    @classmethod
    def _do_resource_update(
        cls, resource: AbstractExternalResource
    ) -> AbstractExternalResource:
        raise NotImplementedError("Child classes must implement _do_resource_update")

    @classmethod
    def _save_resource(cls, resource: AbstractExternalResource):
        raise NotImplementedError("Child classes must implement _save_resource")

    @classmethod
    def activate_resource_for_run(  # type: ignore
        cls, resource: AbstractExternalResource, run_id: str, root_id: str
    ) -> AbstractExternalResource:
        logger.debug("Activating resource '%s' for run '%s'", resource.id, run_id)

        cls._save_resource(resource)
        cls._get_resource_manager().link_resource_to_run(resource.id, run_id, root_id)
        time_started = time.time()

        try:
            resource = cls._do_resource_activate(resource=resource)
        except Exception as e:
            raise ExternalResourceError(
                f"Could not activate resource with id {resource.id}: {e}"
            ) from e

        cls._save_resource(resource=resource)
        activation_timeout_seconds = resource.get_activation_timeout_seconds()

        while resource.status.state != ResourceState.ACTIVE:
            try:
                resource = cls._do_resource_update(resource)
            except Exception as e:
                logger.error(
                    "Error getting latest state from resource %s: %s", resource.id, e
                )
            time.sleep(cls._RESOURCE_UPDATE_INTERVAL_SECONDS)
            cls._save_resource(resource)

            if resource.status.state.is_terminal():
                raise ExternalResourceError(
                    f"Could not activate resource with id {resource.id}: "
                    f"{resource.status.message}"
                )

            if time.time() - time_started > activation_timeout_seconds:
                raise ExternalResourceError(
                    f"Timed out activating resource with id {resource.id}. "
                    f"Last update message: {resource.status.message}"
                )
        return resource

    @classmethod
    def deactivate_resource(  # type: ignore
        cls, resource_id: str
    ) -> AbstractExternalResource:
        logger.debug("Deactivating resource '%s'", resource_id)

        resource = cls._get_resource_manager().get_resource_for_id(resource_id)

        if resource.status.state.is_terminal():
            return resource

        time_started = time.time()
        try:
            resource = cls._do_resource_deactivate(resource=resource)
        except Exception as e:
            raise ExternalResourceError(
                f"Could not deactivate resource with id {resource.id}: {e}"
            ) from e

        cls._save_resource(resource)
        deactivation_timeout_seconds = resource.get_deactivation_timeout_seconds()

        while not resource.status.state.is_terminal():
            try:
                resource = cls._do_resource_update(resource=resource)
            except Exception as e:
                logger.error(
                    "Error getting latest state from resource %s: %s", resource.id, e
                )

            time.sleep(cls._RESOURCE_UPDATE_INTERVAL_SECONDS)
            cls._save_resource(resource=resource)

            if time.time() - time_started > deactivation_timeout_seconds:
                raise ExternalResourceError(
                    f"Timed out deactivating resource with id {resource.id}. "
                    f"Last update message: {resource.status.message}"
                )

        return resource

    def _deactivate_all_resources(self) -> None:
        resources = self._get_resource_manager().resources_by_root_id(
            self._root_future.id
        )

        if len(resources) == 0:
            return

        logger.warning(
            "Deactivating all %s resource(s) due to pipeline run failure.",
            len(resources),
        )

        failed_to_deactivate = []
        for resource in resources:
            try:
                self._do_resource_deactivate(resource=resource)
            except Exception:
                failed_to_deactivate.append(resource.id)

        if len(failed_to_deactivate) > 0:
            logger.error(
                "Failed to deactivate resources with ids: %s",
                ", ".join(failed_to_deactivate),
            )
