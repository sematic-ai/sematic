# Standard Library
import time
from dataclasses import dataclass, replace

# Third-party
import pytest

# Sematic
from sematic.external_resource import (
    ExternalResource,
    IllegalStateTransitionError,
    ResourceState,
    ResourceStatus,
)


def test_update():
    updated_message = "jumping straight to deactivated"

    class FakeImpl(ExternalResource):
        def _do_update(self):
            return replace(
                self,
                status=ResourceStatus(
                    state=ResourceState.DEACTIVATED,
                    message=updated_message,
                    last_update_epoch_time=int(time.time()),
                ),
            )

    with pytest.raises(IllegalStateTransitionError):
        FakeImpl().update()

    updated = FakeImpl(
        status=ResourceStatus(
            state=ResourceState.DEACTIVATING,
            message="tearing down the whatever",
            last_update_epoch_time=int(time.time()),
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
                    last_update_epoch_time=int(time.time()),
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
                    last_update_epoch_time=int(time.time()),
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
                    last_update_epoch_time=int(time.time()),
                ),
            )

    with pytest.raises(IllegalStateTransitionError):
        ValidImpl().deactivate()

    deactivating = ValidImpl(
        status=ResourceStatus(
            state=ResourceState.ACTIVE,
            message="",
            last_update_epoch_time=int(time.time()),
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
                    last_update_epoch_time=int(time.time()),
                ),
            )

    with pytest.raises(IllegalStateTransitionError):
        InvalidImpl().deactivate()


def test_valid_transitions():
    assert ResourceState.CREATED.is_allowed_transition(ResourceState.ACTIVATING)
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
