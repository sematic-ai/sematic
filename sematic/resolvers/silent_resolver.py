# Standard Library
import logging
import time

# Sematic
from sematic.abstract_future import AbstractFuture, FutureState
from sematic.external_resource import ExternalResource, ResourceState
from sematic.future_context import PrivateContext, SematicContext, set_context
from sematic.resolvers.resource_manager import InMemoryResourceManager, ResourceManager
from sematic.resolvers.state_machine_resolver import StateMachineResolver
from sematic.utils.exceptions import (
    InfrastructureError,
    ResolutionError,
    format_exception_for_run,
)

logger = logging.getLogger(__name__)


_RESOURCE_ACTIVATION_TIMEOUT_SECONDS = 600  # 600s => 10 min
_RESOURCE_DEACTIVATION_TIMEOUT_SECONDS = 60  # 60s => 1 min


class SilentResolver(StateMachineResolver):
    """A resolver to resolver a DAG in memory, without tracking to the DB."""

    _resource_manager: ResourceManager = InMemoryResourceManager()

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

    @classmethod
    def activate_resource_for_run(
        cls, resource: ExternalResource, run_id: str, root_id: str
    ) -> ExternalResource:
        cls._resource_manager.save_resource(resource)
        cls._resource_manager.link_resource_to_run(resource.id, run_id, root_id)
        time_started = time.time()
        resource = resource.activate(is_local=True)
        cls._resource_manager.save_resource(resource)
        while resource.status.state != ResourceState.ACTIVE:
            resource = resource.update()
            cls._resource_manager.save_resource(resource)
            if resource.status.state.is_terminal():
                raise InfrastructureError(
                    f"Could not activate resource with id {resource.id}: "
                    f"{resource.status.message}"
                )
            if time.time() - time_started > _RESOURCE_DEACTIVATION_TIMEOUT_SECONDS:
                raise InfrastructureError(
                    f"Timed out activating resource with id {resource.id}. "
                    f"Last update message: {resource.status.message}"
                )
        return resource

    @classmethod
    def deactivate_resource(cls, resource_id: str) -> ExternalResource:
        resource = cls._resource_manager.get_resource_for_id(resource_id)
        if resource.status.state.is_terminal():
            return resource
        time_started = time.time()
        resource = resource.deactivate()
        cls._resource_manager.save_resource(resource)
        while not resource.status.state.is_terminal():
            resource = resource.update()
            cls._resource_manager.save_resource(resource)
            if time.time() - time_started > _RESOURCE_ACTIVATION_TIMEOUT_SECONDS:
                raise InfrastructureError(
                    f"Timed out deactivating resource with id {resource.id}. "
                    f"Last update message: {resource.status.message}"
                )
        return resource
