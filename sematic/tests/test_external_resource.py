# Standard Library
from dataclasses import dataclass, replace

# Third-party
import pytest

# Sematic
from sematic.calculator import func
from sematic.external_resource import (
    ExternalResource,
    IllegalStateTransitionError,
    ResourceState,
    ResourceStatus,
)
from sematic.resolvers.silent_resolver import SilentResolver


def test_update():
    updated_message = "jumping straight to deactivated"

    class FakeImpl(ExternalResource):
        def _do_update(self):
            return replace(
                self,
                status=ResourceStatus(
                    state=ResourceState.DEACTIVATED,
                    message=updated_message,
                ),
            )

    with pytest.raises(IllegalStateTransitionError):
        FakeImpl().update()

    updated = FakeImpl(
        status=ResourceStatus(
            state=ResourceState.DEACTIVATING,
            message="tearing down the whatever",
        )
    ).update()
    assert updated.status.message == updated_message


def test_activate():
    @dataclass(frozen=True)
    class ValidImpl(ExternalResource):
        is_local: bool = False

        def _do_activate(self, is_local):
            return replace(
                self,
                is_local=is_local,
                status=ResourceStatus(
                    state=ResourceState.ACTIVATING,
                    message="updating",
                ),
            )

    activating_local = ValidImpl().activate(True)
    activating_remote = ValidImpl().activate(False)
    assert activating_local.is_local
    assert not activating_remote.is_local

    @dataclass(frozen=True)
    class InvalidImpl(ExternalResource):
        is_local: bool = False

        def _do_activate(self, is_local):
            return replace(
                self,
                is_local=is_local,
                status=ResourceStatus(
                    state=ResourceState.DEACTIVATING,
                    message="updating",
                ),
            )

    with pytest.raises(IllegalStateTransitionError):
        InvalidImpl().activate(True)


def test_deactivate():
    @dataclass(frozen=True)
    class ValidImpl(ExternalResource):
        def _do_deactivate(self):
            return replace(
                self,
                status=ResourceStatus(
                    state=ResourceState.DEACTIVATING,
                    message="updating",
                ),
            )

    with pytest.raises(IllegalStateTransitionError):
        ValidImpl().deactivate()

    deactivating = ValidImpl(
        status=ResourceStatus(
            state=ResourceState.ACTIVE,
            message="",
        )
    ).deactivate()
    assert deactivating.status.state == ResourceState.DEACTIVATING

    @dataclass(frozen=True)
    class InvalidImpl(ExternalResource):
        def _do_deactivate(self):
            return replace(
                self,
                status=ResourceStatus(
                    state=ResourceState.ACTIVE,
                    message="updating",
                ),
            )

    with pytest.raises(IllegalStateTransitionError):
        InvalidImpl().deactivate()


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

    assert not ResourceState.DEACTIVATED.is_allowed_transition(
        ResourceState.DEACTIVATING
    )


def test_use_in_func():
    error_regex = (
        r".*for argument 'resource' of sematic.tests.test_external_resource.my_func"
        r".* inside the body.*"
    )
    with pytest.raises(TypeError, match=error_regex):

        @func
        def my_func(resource: ExternalResource) -> int:
            return 42


@dataclass(frozen=True)
class SomeImpl(ExternalResource):
    my_field: int = 42

    def _do_activate(self, is_local):
        return replace(
            self,
            status=ResourceStatus(
                state=ResourceState.ACTIVATING,
                message="updating",
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
        invalid_use_in_pipeline().resolve(SilentResolver())
    except Exception as e:
        error = e
    assert "SomeImpl" in str(error)
    assert "my_field" in str(error)
    assert "pass_through_int" in str(error)
