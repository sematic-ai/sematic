# Standard library
import typing

# Glow
from glow.abstract_future import AbstractFuture, FutureState
from glow.resolvers.state_machine_resolver import StateMachineResolver


class OfflineResolver(StateMachineResolver):
    """
    A resolver to resolver a DAG locally with no tracking.
    """

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

    def _wait_for_scheduled_run(self) -> None:
        pass
