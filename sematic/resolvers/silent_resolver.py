# Standard Library
import logging

# Sematic
from sematic.abstract_future import AbstractFuture, FutureState
from sematic.external_resource import ResourceState
from sematic.future_context import PrivateContext, SematicContext, set_context
from sematic.resolvers.state_machine_resolver import StateMachineResolver
from sematic.utils.exceptions import ResolutionError, format_exception_for_run

logger = logging.getLogger(__name__)


class SilentResolver(StateMachineResolver):
    """A resolver to resolver a DAG in memory, without tracking to the DB."""

    def _schedule_future(self, future: AbstractFuture) -> None:
        self._activate_resources(future)
        self._run_inline(future)

    def _activate_resources(self, future):
        for resource in future.props.external_resources:
            resource = resource.activate(is_local=True)
            while not (
                resource.status.state == ResourceState.ACTIVE
                or resource.status.state.is_terminal()
            ):
                resource = resource.update()

    def _deactivate_resources(self, future):
        for resource in future.props.external_resources:
            resource = resource.deactivate()
            while not resource.status.state.is_terminal():
                resource = resource.update()

    def _run_inline(self, future: AbstractFuture) -> None:
        self._set_future_state(future, FutureState.SCHEDULED)
        try:
            self._start_inline_execution(future.id)
            with set_context(
                SematicContext(
                    run_id=future.id,
                    root_id=self._root_future.id,
                    private=PrivateContext(
                        resolver_class_path=self.classpath(),
                    ),
                )
            ):
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

    def _future_did_terminate(self, future):
        self._deactivate_resources(future)

    def _wait_for_scheduled_runs(self) -> None:
        pass

    def _register_external_resources(self, future) -> None:
        for external_resource in future.props.external_resources:
            for other_future in self._futures:
                if other_future.id == future.id:
                    continue
                if any(
                    r.id == external_resource.id
                    for r in other_future.props.external_resources
                ):
                    # See https://github.com/sematic-ai/sematic/issues/382
                    use_1 = other_future.calculator.__name__
                    use_2 = future.calculator.__name__
                    raise RuntimeError(
                        f"There is more than one Sematic func in the `with` block for "
                        f"the resource {external_resource}: "
                        f"'{use_1}' and '{use_2}'. At this time, Sematic only supports "
                        f"using resources in one Sematic func. If you like, you may wrap "
                        f"the calls to '{use_1}' and '{use_2}' in an outer func, and "
                        f"place that new func in the `with` block."
                    )
