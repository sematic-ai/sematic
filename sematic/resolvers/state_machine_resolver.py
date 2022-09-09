"""
Abstract base class for a state machine-based resolution.
"""
# Standard Library
import abc
import logging
import typing

# Sematic
from sematic.abstract_calculator import CalculatorError
from sematic.abstract_future import AbstractFuture, FutureState
from sematic.resolver import Resolver

logger = logging.getLogger(__name__)


class StateMachineResolver(Resolver, abc.ABC):
    def __init__(self, detach: bool = False):
        self._futures: typing.List[AbstractFuture] = []
        self._detach = detach

    @property
    def _root_future(self) -> AbstractFuture:
        return self._futures[0]

    def resolve(self, future: AbstractFuture) -> typing.Any:
        try:
            resolved_kwargs = self._get_resolved_kwargs(future)
            if not len(resolved_kwargs) == len(future.kwargs):
                raise ValueError(
                    "All input arguments of your root function should be concrete."
                )

            future.resolved_kwargs = resolved_kwargs

            self._enqueue_future(future)

            if self._detach:
                return self._detach_resolution(future)

            self._resolution_will_start()

            while future.state != FutureState.RESOLVED:
                for future_ in self._futures:
                    if future_.state == FutureState.CREATED:
                        self._schedule_future_if_args_resolved(future_)
                    if future_.state == FutureState.RAN:
                        self._resolve_nested_future(future_)

                self._wait_for_scheduled_run()

            self._resolution_did_succeed()

            if future.state != FutureState.RESOLVED:
                raise RuntimeError("Unresolved Future after resolver call.")

            return future.value
        except Exception as e:
            self._resolution_did_fail(error=e)
            if isinstance(e, CalculatorError) and hasattr(e, "__cause__"):
                # this will simplify the stack trace so the user sees less
                # from Sematic's stack and more from the error from their code.
                raise e.__cause__  # type: ignore
            raise e

    def _detach_resolution(self, future: AbstractFuture) -> str:
        raise NotImplementedError()

    def _enqueue_future(self, future: AbstractFuture) -> None:
        if future in self._futures:
            return

        self._futures.append(future)

        for value in future.kwargs.values():
            if isinstance(value, AbstractFuture):
                value.parent_future = future.parent_future
                self._enqueue_future(value)

    @abc.abstractmethod
    def _schedule_future(self, future: AbstractFuture):
        pass

    @abc.abstractmethod
    def _run_inline(self, future: AbstractFuture):
        pass

    @abc.abstractmethod
    def _wait_for_scheduled_run(self) -> None:
        pass

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

        This is called after all futures have succesfully resolved.
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

    @staticmethod
    def _get_resolved_kwargs(future: AbstractFuture) -> typing.Dict[str, typing.Any]:
        """
        Extract only resolved/concrete kwargs
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
            self._future_will_schedule(future)
            if future.props.inline:
                logger.info("Running inline {}".format(future.calculator))
                self._run_inline(future)
            else:
                logger.info("Scheduling {}".format(future.calculator))
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

    def _handle_future_failure(self, future: AbstractFuture, exception: Exception):
        """
        When a future fails, its state machine as well as that of its parent
        futures need to be updated.

        Additionally (not yet implemented) the stack trace needs to be persisted
        in order to display in the UI.
        """
        self._fail_future_and_parents(future)
        raise exception

    def _fail_future_and_parents(
        self,
        future: AbstractFuture,
    ):
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
        except TypeError as exception:
            self._handle_future_failure(future, exception)

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
        Setting a nested future on a RAN future
        """
        future.nested_future = nested_future
        nested_future.parent_future = future
        self._enqueue_future(nested_future)
