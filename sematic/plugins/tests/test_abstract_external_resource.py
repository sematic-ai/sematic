# Standard Library
from dataclasses import dataclass, replace

# Third-party
import pytest

# Sematic
from sematic.function import func
from sematic.plugins.abstract_external_resource import (
    AbstractExternalResource,
    IllegalStateTransitionError,
    ManagedBy,
    ResourceState,
    ResourceStatus,
)
from sematic.runners.silent_runner import SilentRunner


def test_update():
    updated_message = "jumping straight to ACTIVE"

    class FakeImpl(AbstractExternalResource):
        def _do_update(self):
            return replace(
                self,
                status=ResourceStatus(
                    state=ResourceState.ACTIVE,
                    message=updated_message,
                    managed_by=ManagedBy.RESOLVER,
                ),
            )

    with pytest.raises(IllegalStateTransitionError):
        FakeImpl().update()

    updated = FakeImpl(
        status=ResourceStatus(
            state=ResourceState.ACTIVATING,
            message="spinning up the whatever",
            managed_by=ManagedBy.RESOLVER,
        )
    ).update()
    assert updated.status.message == updated_message


def test_activate() -> None:
    @dataclass(frozen=True)
    class ValidImpl(AbstractExternalResource):
        is_local: bool = False

        def _do_activate(self, is_local):
            return replace(
                self,
                is_local=is_local,
                status=ResourceStatus(
                    state=ResourceState.ACTIVATING,
                    message="updating",
                    managed_by=ManagedBy.RESOLVER if is_local else ManagedBy.SERVER,
                ),
            )

    activating_local = ValidImpl().activate(True)
    activating_remote = ValidImpl().activate(False)
    assert activating_local.is_local  # type: ignore
    assert not activating_remote.is_local  # type: ignore

    @dataclass(frozen=True)
    class InvalidImpl(AbstractExternalResource):
        is_local: bool = False

        def _do_activate(self, is_local):
            return replace(
                self,
                is_local=is_local,
                status=ResourceStatus(
                    state=ResourceState.CREATED,
                    message="updating",
                    managed_by=ManagedBy.RESOLVER if is_local else ManagedBy.SERVER,
                ),
            )

    with pytest.raises(IllegalStateTransitionError):
        InvalidImpl().activate(True)


def test_deactivate():
    @dataclass(frozen=True)
    class ValidImpl(AbstractExternalResource):
        def _do_deactivate(self):
            return replace(
                self,
                status=ResourceStatus(
                    state=ResourceState.DEACTIVATING,
                    message="updating",
                    managed_by=ManagedBy.RESOLVER,
                ),
            )

    deactivating = ValidImpl(
        status=ResourceStatus(
            state=ResourceState.ACTIVE,
            message="",
            managed_by=ManagedBy.RESOLVER,
        )
    ).deactivate()
    assert deactivating.status.state == ResourceState.DEACTIVATING

    @dataclass(frozen=True)
    class InvalidImpl(AbstractExternalResource):
        def _do_deactivate(self):
            return replace(
                self,
                status=ResourceStatus(
                    state=ResourceState.ACTIVE,
                    message="updating",
                    managed_by=ManagedBy.RESOLVER,
                ),
            )

    with pytest.raises(IllegalStateTransitionError):
        InvalidImpl(
            status=ResourceStatus(
                state=ResourceState.ACTIVE,
                message="",
                managed_by=ManagedBy.RESOLVER,
            )
        ).deactivate()


def test_valid_transitions():
    assert ResourceState.CREATED.is_allowed_transition(ResourceState.ACTIVATING)
    assert ResourceState.CREATED.is_allowed_transition(ResourceState.DEACTIVATED)
    assert not ResourceState.CREATED.is_allowed_transition(ResourceState.ACTIVE)

    assert ResourceState.ACTIVATING.is_allowed_transition(ResourceState.ACTIVE)
    assert ResourceState.ACTIVATING.is_allowed_transition(ResourceState.DEACTIVATING)
    assert not ResourceState.ACTIVATING.is_allowed_transition(ResourceState.CREATED)

    assert ResourceState.ACTIVE.is_allowed_transition(ResourceState.DEACTIVATING)
    assert not ResourceState.ACTIVE.is_allowed_transition(ResourceState.DEACTIVATED)

    assert ResourceState.DEACTIVATING.is_allowed_transition(ResourceState.DEACTIVATED)
    assert not ResourceState.DEACTIVATING.is_allowed_transition(ResourceState.ACTIVE)

    assert not ResourceState.DEACTIVATED.is_allowed_transition(ResourceState.DEACTIVATING)


def test_use_in_func():
    error_regex = r".* inside the body.*parameter 'resource'.*"
    with pytest.raises(TypeError, match=error_regex):

        @func
        def my_func(resource: AbstractExternalResource) -> int:
            return 42


@dataclass(frozen=True)
class SomeImpl(AbstractExternalResource):
    my_field: int = 42

    def _do_activate(self, is_local):
        return replace(
            self,
            status=ResourceStatus(
                state=ResourceState.ACTIVATING,
                message="updating",
                managed_by=ManagedBy.RESOLVER,
            ),
        )


@func
def pass_through_int(x: int) -> int:
    return x


@func
def invalid_use_in_pipeline() -> int:
    intermediate = pass_through_int(42)
    with SomeImpl(my_field=intermediate):
        return pass_through_int(intermediate)


def test_using_future():
    error = None
    try:
        SilentRunner().run(invalid_use_in_pipeline())
    except Exception as e:
        error = e
    assert "SomeImpl" in str(error)
    assert "my_field" in str(error)
    assert "pass_through_int" in str(error)
