# Standard library
import logging
import typing

# Glow
from glow.abstract_future import AbstractFuture
from glow.resolver import Resolver
from glow.future import FutureState


logger = logging.getLogger(__name__)


class LocalResolver(Resolver):
    """
    A resolver to resolver a DAG locally.
    """

    def __init__(self) -> None:
        self._futures: typing.List[AbstractFuture] = []

    def resolve(self, future: AbstractFuture) -> typing.Any:
        self._enqueue_future(future)

        while future.state != FutureState.RESOLVED:
            for future_ in self._futures:
                if future_.state == FutureState.CREATED:
                    self._schedule_future_if_input_ready(future_)
                if future_.state == FutureState.RAN:
                    self._resolve_nested_future(future_)

            self._wait_for_any_run()

        return future.value

    def _enqueue_future(self, future: AbstractFuture) -> None:
        if future in self._futures:
            return

        self._futures.append(future)
        for value in future.kwargs.values():
            if isinstance(value, AbstractFuture):
                value.parent_future = future.parent_future
                self._enqueue_future(value)

    def _schedule_future_if_input_ready(self, future: AbstractFuture) -> None:
        kwargs = {}
        for name, value in future.kwargs.items():
            if isinstance(value, AbstractFuture):
                if value.state == FutureState.RESOLVED:
                    kwargs[name] = value.value
            else:
                kwargs[name] = value

        all_args_resolved = len(kwargs) == len(future.kwargs)
        if all_args_resolved:
            if future.inline:
                logger.info("Running inline {}".format(future.calculator))
                self._run_inline(future, kwargs)
            else:
                logger.info("Scheduling {}".format(future.calculator))
                self._schedule_run(future, kwargs)

    def _resolve_nested_future(self, future: AbstractFuture) -> None:
        if future.nested_future is None:
            raise RuntimeError("No nested future")

        nested_future = future.nested_future
        nested_future.parent_future = future
        if nested_future.state == FutureState.RESOLVED:
            future.value = nested_future.value
            self._set_future_state(future, FutureState.RESOLVED)

    def _wait_for_any_run(self) -> None:
        pass

    def _schedule_run(
        self, future: AbstractFuture, kwargs: typing.Dict[str, typing.Any]
    ) -> None:
        self._run_inline(future, kwargs)

    def _run_inline(
        self, future: AbstractFuture, kwargs: typing.Dict[str, typing.Any]
    ) -> None:
        self._set_future_state(future, FutureState.SCHEDULED)
        value = future.calculator.calculate(**kwargs)
        cast_value = future.calculator.cast_output(value)
        self._update_future_with_value(future, cast_value)

    def _update_future_with_value(self, future: AbstractFuture, value: typing.Any):
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

    def _set_future_state(
        self, future: AbstractFuture, future_state: FutureState
    ) -> None:
        future.state = future_state
