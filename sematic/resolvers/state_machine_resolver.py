"""
Abstract base class for a state machine-based resolution.
"""
# Standard library
import abc
import logging
import typing

# Sematic
from sematic.abstract_future import AbstractFuture, FutureState
from sematic.resolver import Resolver


logger = logging.getLogger(__name__)


class StateMachineResolver(Resolver, abc.ABC):
    def __init__(self, detach: bool = False):
        self._futures: typing.List[AbstractFuture] = []
        self._detach = detach

    def resolve(self, future: AbstractFuture) -> typing.Any:
        resolved_kwargs = self._get_resolved_kwargs(future)
        if not len(resolved_kwargs) == len(future.kwargs):
            raise ValueError(
                "All input arguments of your root function should be concrete."
            )

        future.resolved_kwargs = resolved_kwargs

        self._resolution_will_start()

        self._enqueue_future(future)

        if self._detach:
            return self._detach_resolution(future)

        while future.state != FutureState.RESOLVED:
            for future_ in self._futures:
                if future_.state == FutureState.CREATED:
                    self._schedule_future_if_input_ready(future_)
                if future_.state == FutureState.RAN:
                    self._resolve_nested_future(future_)

            self._wait_for_scheduled_run()

        self._resolution_did_succeed()

        if future.state != FutureState.RESOLVED:
            raise RuntimeError("Unresolved Future after resolver call.")

        return future.value

    def _detach_resolution(self, future: AbstractFuture) -> str:
        raise NotImplementedError()

    def _enqueue_future(self, future: AbstractFuture) -> None:
        if future in self._futures:
            return

        self._validate_resources(future)
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

    def _validate_resources(self, future: AbstractFuture):
        """Confirm that the future can be run, raise an appropriate exception otherwise.

        Is intended for any resolver-specific constraints. For example, the remote
        resolver can check whether the cloud resources available can meet the
        resource requirements the future has expressed.

        Parameters
        ----------
        future:
            The future to validate.
        """
        pass

    @typing.final
    def _set_future_state(self, future, state):
        # type: (AbstractFuture, FutureState) -> None
        """
        Sets state on future and call corresponding callback.

        **This method must always be used in place of setting state manually.**

        This method could also contain logic to validate allowed state transitions.

        Parameters
        ----------
        future: Future
            Future whose state to set
        state: FutureState
            State to set on future

        Raises
        ------
        ValueError
            If attempting to set state to the same as current state.
        """
        # if state == future.state:
        #    raise ValueError("Future already has state {}".format(state))

        # This is the only location where the setting a future's state
        # is allowed. Setting it elsewhere would forego callbacks.
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

    def _resolution_did_fail(self) -> None:
        """
        Callback allowing resolvers to implement custom actions.

        This is called after a future has failed and the exception is about to be raised.
        """
        pass

    def _future_did_schedule(self, future: AbstractFuture) -> None:
        """
        Callback allowing resolvers to implement custom actions.

        This is called after a future was scheduled.

        Parameters
        ----------
        future: Future
            The scheduled future
        """
        pass

    def _future_did_run(self, future: AbstractFuture) -> None:
        pass

    def _future_did_fail(self, failed_future: AbstractFuture) -> None:
        """Callback allowing specific resolvers to react when a future is marked failed.

        Parameters
        ----------
        failed_future:
            The future that failed
        """
        pass

    def _future_did_resolve(self, future: AbstractFuture) -> None:
        """Callback allowing specific resolvers to react when a future is marked resolved.

        Parameters
        ----------
        future:
            The future that resolved
        """
        pass

    def _future_did_enqueue_for_reschedule(self, future: AbstractFuture) -> None:
        """
        Callback allowing specific resolvers to react when a future is marked enqueued
        for reschedule.

        Parameters
        ----------
        future:
            The future that enqueued for reschedule
        """
        pass

    def _future_will_schedule(self, future: AbstractFuture) -> None:
        """Callback allowing specific resolvers to react when a future is about to be scheduled.

        Parameters
        ----------
        future:
            The future that is about to be scheduled
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
    def _schedule_future_if_input_ready(self, future: AbstractFuture) -> None:
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
        Mark the future FAILED and its parent futures NESTED_FAILED, up
        to `up_to_future` future.

        Parameters
        ----------
        future : Future
            Future instance to be marked `FAILED` state.
        up_to_future : typing.Optional[Future]
            Parent future instance to stop marking `NESTED_FAILED` state. If `None`,
            mark parent future `NESTED_FAILED` all the way to the top of the DAG.
        """
        self._set_future_state(future, FutureState.FAILED)

        parent_future = future.parent_future
        while parent_future is not None:
            self._set_future_state(parent_future, FutureState.NESTED_FAILED)
            parent_future = parent_future.parent_future

    def _update_future_with_value(
        self, future: AbstractFuture, value: typing.Any
    ) -> None:
        value = future.calculator.cast_output(value)

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
