# Standard library
import datetime
import typing

# Glow
from glow.abstract_future import AbstractFuture, FutureState
from glow.db.db import db
from glow.db.models.run import Run
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

    def _future_did_schedule(self, future: AbstractFuture) -> None:
        super()._future_did_schedule(future)
        run = Run(
            id=future.id,
            future_state=FutureState.SCHEDULED.value,
            # todo(@neutralino1): replace with future name
            name=future.calculator.__name__,
            calculator_path="{}.{}".format(
                future.calculator.__module__, future.calculator.__name__
            ),
            parent_id=(
                future.parent_future.id if future.parent_future is not None else None
            ),
            started_at=datetime.datetime.utcnow(),
        )
        with db().get_session() as session:
            session.add(run)
            session.flush()
