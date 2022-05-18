# Standard library
import datetime

# Glow
from glow.abstract_future import AbstractFuture, FutureState
from glow.db.queries import (
    get_run,
    save_run,
    create_run_with_artifacts,
    set_run_output_artifact,
)
from glow.resolvers.state_machine_resolver import StateMachineResolver
from glow.db.models.factories import make_artifact, make_run_from_future


class OfflineResolver(StateMachineResolver):
    """
    A resolver to resolver a DAG locally.
    """

    def _schedule_future(self, future: AbstractFuture) -> None:
        self._run_inline(future)

    def _run_inline(self, future: AbstractFuture) -> None:
        self._set_future_state(future, FutureState.SCHEDULED)
        try:
            value = future.calculator.calculate(**future.resolved_kwargs)
            cast_value = future.calculator.cast_output(value)
            self._update_future_with_value(future, cast_value)
        except Exception as exception:
            self._handle_future_failure(future, exception)

    def _wait_for_scheduled_run(self) -> None:
        pass

    def _future_will_schedule(self, future: AbstractFuture) -> None:
        super()._future_will_schedule(future)

        run = make_run_from_future(future)
        run.future_state = FutureState.SCHEDULED.value
        run.started_at = datetime.datetime.utcnow()

        artifacts = {
            name: make_artifact(value, future.calculator.input_types[name])
            for name, value in future.resolved_kwargs.items()
        }

        create_run_with_artifacts(run, artifacts)

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

        output_artifact = make_artifact(future.value, future.calculator.output_type)

        set_run_output_artifact(run, output_artifact)

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
