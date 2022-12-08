# Standard Library
import time
from dataclasses import dataclass, replace
from typing import List, Optional, Tuple
from unittest import mock

# Third-party
import pytest

# Sematic
from sematic.external_resource import ExternalResource, ResourceState, ResourceStatus
from sematic.tests.fixtures import MockStorage


@pytest.fixture
def mock_local_resolver_storage():
    mock_storage = MockStorage()
    with mock.patch(
        "sematic.resolvers.local_resolver.LocalStorage", return_value=mock_storage
    ):
        yield mock_storage


@pytest.fixture
def mock_cloud_resolver_storage():
    mock_storage = MockStorage()
    with mock.patch(
        "sematic.resolvers.cloud_resolver.S3Storage", return_value=mock_storage
    ):
        yield mock_storage


_fake_resource_history: List["FakeExternalResource"] = []
_fake_resource_call_history: List[Tuple["FakeExternalResource", str]] = []


@dataclass(frozen=True)
class FakeExternalResource(ExternalResource):
    some_field: int = 0

    @classmethod
    def reset_history(cls) -> None:
        _fake_resource_history.clear()
        _fake_resource_call_history.clear()

    @classmethod
    def all_resource_ids(cls) -> List[str]:
        return list({r.id for r in _fake_resource_history})

    @classmethod
    def history_by_id(cls, resource_id: Optional[str]) -> List["FakeExternalResource"]:
        return [
            r
            for r in _fake_resource_history
            if resource_id is None or r.id == resource_id
        ]

    @classmethod
    def call_history_by_id(cls, resource_id: Optional[str]) -> List[str]:
        return [
            call
            for r, call in _fake_resource_call_history
            if resource_id is None or r.id == resource_id
        ]

    def __post_init__(self):
        result = super().__post_init__()
        _fake_resource_history.append(self)
        return result

    def use_resource(self) -> int:
        _fake_resource_call_history.append((self, "use_resource()"))
        if self.status.state != ResourceState.ACTIVE:
            raise RuntimeError(f"Resource used while in the state: {self.status.state}")
        return self.some_field

    def _do_activate(self, is_local: bool):
        _fake_resource_call_history.append((self, f"_do_activate({is_local})"))
        return replace(
            self,
            status=ResourceStatus(
                state=ResourceState.ACTIVATING,
                message="Allocating fake resource",
                last_update_epoch_time=int(time.time()),
            ),
        )

    def _do_deactivate(self):
        _fake_resource_call_history.append((self, "_do_deactivate()"))
        return replace(
            self,
            status=ResourceStatus(
                state=ResourceState.DEACTIVATING,
                message="Deallocating fake resource",
                last_update_epoch_time=int(time.time()),
            ),
        )

    def _do_update(self) -> "FakeExternalResource":
        _fake_resource_call_history.append((self, "_do_update()"))
        if self.status.state == ResourceState.ACTIVATING:
            return replace(
                self,
                status=ResourceStatus(
                    state=ResourceState.ACTIVE,
                    message="Resource is ready!",
                    last_update_epoch_time=int(time.time()),
                ),
            )
        elif self.status.state == ResourceState.DEACTIVATING:
            return replace(
                self,
                status=ResourceStatus(
                    state=ResourceState.DEACTIVATED,
                    message="Resource is cleaned!",
                    last_update_epoch_time=int(time.time()),
                ),
            )
        return replace(
            self,
            status=ResourceStatus(
                state=self.status.state,
                message="Nothing has changed...",
                last_update_epoch_time=int(time.time()),
            ),
        )
