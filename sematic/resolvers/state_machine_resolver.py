"""
Abstract base class for a state machine-based resolution.
"""
# Standard Library
import abc
import logging
import signal
import typing
from contextlib import contextmanager

# Sematic
from sematic.abstract_calculator import CalculatorError
from sematic.abstract_future import AbstractFuture, FutureState
from sematic.resolver import Resolver
from sematic.utils.exceptions import (
    ExceptionMetadata,
    ResolutionError,
    format_exception_for_run,
)

logger = logging.getLogger(__name__)


class StateMachineResolver(Resolver, abc.ABC):
    def __init__(self):
        self._futures: typing.List[AbstractFuture] = []

    @property
    def _root_future(self) -> AbstractFuture:
        if len(self._futures) == 0:
            raise RuntimeError("No root future: no futures were enqueued.")

        return self._futures[0]

    def resolve(self, future: AbstractFuture) -> typing.Any:
        with self._catch_resolution_errors():
            self._seed_graph(future)
            self._resolution_loop()

        return self._root_future.value

    def _seed_graph(self, future):
        """
        Set the initial futures for the resolution.

        This is a stub that can be
        overridden by child classes. The resolver will evolve the DAG using this initial
        set of futures. The root future should always be element 0 of `self._futures`,
        there are no requirements on order of other futures. The default implementation
        just seeds with the root future itself and no others.
        """
        self._enqueue_root_future(future)

    def _resolution_loop(self):
        """
        Assuming that the future graph was seeded, this method will proceed
        through the graph until the root future is resolved.
        """
        self._register_signal_handlers()

        logger.info(f"Starting resolution {self._root_future.id}")

        self._resolution_will_start()

        while not self._root_future.state.is_terminal():
            for future_ in self._futures:
                if future_.state == FutureState.CREATED:
                    self._schedule_future_if_args_resolved(future_)
                    continue
                if future_.state == FutureState.RETRYING:
                    self._execute_future(future_)
                    continue
                if future_.state == FutureState.RAN:
                    self._resolve_nested_future(future_)
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

            self._wait_for_scheduled_runs()

        if self._root_future.state == FutureState.RESOLVED:
            self._resolution_did_succeed()
        elif self._root_future.state == FutureState.CANCELED:
            return
        else:
            raise RuntimeError("Unresolved Future after resolver call.")

    @contextmanager
    def _catch_resolution_errors(self):
        try:
            yield
        except Exception as e:
            self._resolution_did_fail(error=e)
            if isinstance(e, CalculatorError) and hasattr(e, "__cause__"):
                # this will simplify the stack trace so the user sees less
                # from Sematic's stack and more from the error from their code.
                raise e.__cause__  # type: ignore
            raise e

    def _enqueue_root_future(self, future: AbstractFuture):
        resolved_kwargs = self._get_resolved_kwargs(future)
        if not len(resolved_kwargs) == len(future.kwargs):
            raise ValueError(
                "All input arguments of your root function should be concrete."
            )

        future.resolved_kwargs = resolved_kwargs

        # Cleaning up
        self._futures.clear()

        self._enqueue_future(future)

    def _register_signal_handlers(self):
        for signum in {signal.SIGINT, signal.SIGTERM}:
            signal.signal(signum, self._handle_sig_cancel)

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

    def _handle_sig_cancel(self, signum, frame):
        logger.warning("Received SIGINT, canceling resolution...")
        self._resolution_did_cancel()

    def _cancel_non_terminal_futures(self):
        for future in self._futures:
            if not future.state.is_terminal():
                self._set_future_state(future, FutureState.CANCELED)

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
            FutureState.RESOLVED: self._future_did_resolve,
            FutureState.RETRYING: self._future_did_get_marked_for_retry,
        }

        if state in CALLBACKS:
            CALLBACKS[state](future)

    # State machine lifecycle hooks

    def _resolution_will_start(self) -> None:
        """
        Callback allowing resolvers to implement custom actions.

        This is called when `resolve` has been called and
        before any future get scheduled for resolution.
        """
        pass

    def _resolution_did_succeed(self) -> None:
        """
        Callback allowing resolvers to implement custom actions.

        This is called after all futures have successfully resolved.
        """
        pass

    def _resolution_did_fail(self, error: Exception) -> None:
        """
        Callback allowing resolvers to implement custom actions.

        This is called after a future has failed and the exception is about to be raised.

        Parameters
        ----------
        error:
            The error that led to the resolution's failure. If the error occurred
            within a calculator, will be an instance of CalculatorError
        """
        pass

    def _resolution_did_cancel(self) -> None:
        pass

    def _future_did_schedule(self, future: AbstractFuture) -> None:
        """
        Callback allowing resolvers to implement custom actions.

        This is called after a future was scheduled.
        """
        pass

    def _future_did_run(self, future: AbstractFuture) -> None:
        pass

    def _future_did_fail(self, failed_future: AbstractFuture) -> None:
        """
        Callback allowing specific resolvers to react when a future is marked failed.
        """
        pass

    def _future_did_resolve(self, future: AbstractFuture) -> None:
        """
        Callback allowing specific resolvers to react when a future is marked resolved.
        """
        pass

    def _future_will_schedule(self, future: AbstractFuture) -> None:
        """
        Callback allowing specific resolvers to react when a future is about to
        be scheduled.
        """
        pass

    def _future_did_get_marked_for_retry(self, future: AbstractFuture) -> None:
        """
        Callback allowing specific resolvers to react when a future is about to
        be retried.
        """
        pass

    @staticmethod
    def _get_resolved_kwargs(future: AbstractFuture) -> typing.Dict[str, typing.Any]:
        """
        Extract only resolved/concrete kwargs.
        """
        resolved_kwargs = {}
        for name, value in future.kwargs.items():
            if isinstance(value, AbstractFuture):
                if value.state == FutureState.RESOLVED:
                    resolved_kwargs[name] = value.value
            else:
                resolved_kwargs[name] = value

        return resolved_kwargs

    @typing.final
    def _schedule_future_if_args_resolved(self, future: AbstractFuture) -> None:
        resolved_kwargs = self._get_resolved_kwargs(future)

        all_args_resolved = len(resolved_kwargs) == len(future.kwargs)

        if all_args_resolved:
            future.resolved_kwargs = resolved_kwargs
            self._execute_future(future)

    def _execute_future(self, future: AbstractFuture) -> None:
        if not self._can_schedule_future(future):
            logger.info("Currently not scheduling %s", future.calculator)
            return

        self._future_will_schedule(future)

        if future.props.inline:
            logger.info("Running inline %s %s", future.id, future.calculator)
            self._run_inline(future)
        else:
            logger.info("Scheduling %s %s", future.id, future.calculator)
            self._schedule_future(future)

    @typing.final
    def _resolve_nested_future(self, future: AbstractFuture) -> None:
        if future.nested_future is None:
            raise RuntimeError("No nested future")

        nested_future = future.nested_future
        nested_future.parent_future = future
        if nested_future.state == FutureState.RESOLVED:
            future.value = nested_future.value
            self._set_future_state(future, FutureState.RESOLVED)

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
            (Pipeline, Resolver, Driver)
        external_exception_metadata:
            Metadata describing an exception which occurred in external compute
            infrastructure
        """
        retry_settings = future.props.retry_settings

        if retry_settings is None:
            logging.info(f"No retries configured for {future.id}, failing now.")
            self._fail_future_and_parents(future)
            raise ResolutionError(exception_metadata, external_exception_metadata)

        if not retry_settings.should_retry(
            exception_metadata, external_exception_metadata
        ):
            logging.info(
                "Retries exhausted or exception not retriable for "
                f"{future.id}, failing now."
            )
            self._fail_future_and_parents(future)
            raise ResolutionError(exception_metadata, external_exception_metadata)

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
            value = future.calculator.cast_output(value)
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
