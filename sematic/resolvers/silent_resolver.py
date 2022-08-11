# Standard Library
import logging

# Sematic
from sematic.abstract_future import AbstractFuture, FutureState
from sematic.resolvers.state_machine_resolver import StateMachineResolver

logger = logging.getLogger(__name__)


class SilentResolver(StateMachineResolver):
    """
    A resolver to resolver a DAG in memory, without tracking to the DB.
    """

    def _schedule_future(self, future: AbstractFuture) -> None:
        self._run_inline(future)

    def _run_inline(self, future: AbstractFuture) -> None:
        self._set_future_state(future, FutureState.SCHEDULED)
        try:
            value = future.calculator.calculate(**future.resolved_kwargs)
            self._update_future_with_value(future, value)
        except Exception as exception:
            self._handle_future_failure(future, exception)

    def _wait_for_scheduled_run(self) -> None:
        pass
