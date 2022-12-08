# Standard Library
import logging

# Sematic
from sematic.abstract_future import AbstractFuture, FutureState
from sematic.future_context import PrivateContext, SematicContext, set_context
from sematic.plugins.abstract_external_resource import AbstractExternalResource
from sematic.resolvers.abstract_resource_manager import AbstractResourceManager
from sematic.resolvers.resource_managers.memory_manager import MemoryResourceManager
from sematic.resolvers.state_machine_resolver import StateMachineResolver
from sematic.utils.exceptions import ResolutionError, format_exception_for_run

logger = logging.getLogger(__name__)


class SilentResolver(StateMachineResolver):
    """A `Resolver` that resolves a pipeline in memory, without tracking to the DB."""

    _resource_manager: AbstractResourceManager = MemoryResourceManager()

    def _schedule_future(self, future: AbstractFuture) -> None:
        self._run_inline(future)

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
