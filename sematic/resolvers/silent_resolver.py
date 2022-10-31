# Standard Library
import logging

# Sematic
from sematic.abstract_future import AbstractFuture, FutureState
from sematic.resolvers.state_machine_resolver import StateMachineResolver
from sematic.utils.exceptions import ResolutionError, format_exception_for_run

logger = logging.getLogger(__name__)


class SilentResolver(StateMachineResolver):
    """A resolver to resolver a DAG in memory, without tracking to the DB."""

    def _schedule_future(self, future: AbstractFuture) -> None:
        self._run_inline(future)

    def _run_inline(self, future: AbstractFuture) -> None:
        self._set_future_state(future, FutureState.SCHEDULED)
        try:
            self._start_inline_execution(future.id)
            value = future.calculator.calculate(**future.resolved_kwargs)
            self._update_future_with_value(future, value)
        except ResolutionError:
            # only we raise ResolutionError when determining a failure is unrecoverable
            # if we got this exception type, then the failure has already been properly
            # handled and all is left to do is to terminate the execution.
            raise
        except Exception as e:
            logger.error("Error executing future", exc_info=e)
            self._handle_future_failure(future, format_exception_for_run(e))
        finally:
            self._end_inline_execution(future.id)

    def _start_inline_execution(self, future_id) -> None:
        """Callback called before an inline execution."""
        pass

    def _end_inline_execution(self, future_id) -> None:
        """Callback called at the end of an inline execution."""
        pass

    def _wait_for_scheduled_runs(self) -> None:
        pass
