# Standard library
import datetime
import typing

# Glow
from glow.abstract_future import AbstractFuture, FutureState
from glow.db.queries import create_run, get_run, save_run
from glow.db.models.run import Run
from glow.resolvers.state_machine_resolver import StateMachineResolver


class OfflineResolver(StateMachineResolver):
    """
    A resolver to resolver a DAG locally.
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

        create_run(run)

    def _future_did_run(self, future: AbstractFuture) -> None:
        super()._future_did_run(future)

        run = get_run(future.id)

        if future.parent_future is not None:
            run.parent_id = future.parent_future.id

        run.future_state = FutureState.RAN.value
        run.ended_at = datetime.datetime.utcnow()

        save_run(run)

    def _future_did_resolve(self, future: AbstractFuture) -> None:
        super()._future_did_resolve(future)

        run = get_run(future.id)

        run.future_state = FutureState.RESOLVED.value
        run.resolved_at = datetime.datetime.utcnow()
        if run.ended_at is None:
            run.ended_at = run.resolved_at

        save_run(run)

    def _future_did_fail(self, failed_future: AbstractFuture) -> None:
        super()._future_did_fail(failed_future)

        run = get_run(failed_future.id)

        run.future_state = (
            FutureState.NESTED_FAILED.value
            if failed_future.nested_future is not None
            and failed_future.state in (FutureState.FAILED, FutureState.NESTED_FAILED)
            else FutureState.FAILED.value
        )
        run.failed_at = datetime.datetime.utcnow()

        save_run(run)
