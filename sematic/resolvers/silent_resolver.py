# Standard Library
import logging

# Sematic
from sematic.abstract_future import (
    AbstractFuture,
    FutureState,
    get_minimum_call_chain_timeout_seconds,
)
from sematic.future_context import PrivateContext, SematicContext, set_context
from sematic.plugins.abstract_external_resource import AbstractExternalResource
from sematic.resolvers.abstract_resource_manager import AbstractResourceManager
from sematic.resolvers.resource_managers.memory_manager import MemoryResourceManager
from sematic.resolvers.state_machine_resolver import StateMachineResolver
from sematic.utils.exceptions import (
    ResolutionError,
    TimeoutError,
    format_exception_for_run,
)
from sematic.utils.timeout import timeout

logger = logging.getLogger(__name__)


class SilentResolver(StateMachineResolver):
    """A `Resolver` that resolves a pipeline in memory, without tracking to the DB."""

    _resource_manager: AbstractResourceManager = MemoryResourceManager()

    def _schedule_future(self, future: AbstractFuture) -> None:
        self._run_inline(future)

    def _run_inline(self, future: AbstractFuture) -> None:
        self._set_future_state(future, FutureState.SCHEDULED)
        (
            timeout_seconds,
            timeout_restricting_future,
        ) = get_minimum_call_chain_timeout_seconds(future)
        timeout_seconds = None if timeout_seconds is None else int(timeout_seconds)
        if (
            timeout_seconds is not None
            and timeout_seconds < 0
            and timeout_restricting_future is not None
        ):
            self._fail_future_with_timeout(timeout_restricting_future)
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
                try:
                    with timeout(timeout_seconds):
                        value = future.calculator.calculate(**future.resolved_kwargs)
                except TimeoutError:
                    self._fail_future_with_timeout(future, timeout_restricting_future)
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

    def _resolution_did_fail(self, error: Exception) -> None:
        self._deactivate_all_resources()

    @classmethod
    def _do_resource_activate(
        cls, resource: AbstractExternalResource
    ) -> AbstractExternalResource:
        resource = resource.activate(is_local=True)
        return resource

    @classmethod
    def _do_resource_deactivate(
        cls, resource: AbstractExternalResource
    ) -> AbstractExternalResource:
        resource = resource.deactivate()
        return resource

    @classmethod
    def _do_resource_update(
        cls, resource: AbstractExternalResource
    ) -> AbstractExternalResource:
        resource = resource.update()
        return resource

    @classmethod
    def _save_resource(cls, resource: AbstractExternalResource):
        cls._get_resource_manager().save_resource(resource)

    @classmethod
    def _get_resource_manager(cls) -> AbstractResourceManager:
        return cls._resource_manager
