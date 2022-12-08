# Third-party
import pytest

# Sematic
from sematic.abstract_calculator import CalculatorError
from sematic.abstract_future import FutureState
from sematic.calculator import func
from sematic.external_resource import ResourceState
from sematic.future_context import SematicContext, context
from sematic.resolvers.silent_resolver import SilentResolver
from sematic.resolvers.tests.fixtures import FakeExternalResource
from sematic.retry_settings import RetrySettings
from sematic.utils.exceptions import ResolutionError


@func
def add(a: float, b: float) -> float:
    return a + b


@func
def add3(a: float, b: float, c: float) -> float:
    return add(add(a, b), c)


@func
def pipeline(a: float, b: float) -> float:
    c = add(a, b)
    d = add3(a, b, c)
    return add(c, d)


@func
def context_pipeline() -> SematicContext:
    return direct_context_func()


@func
def direct_context_func() -> SematicContext:
    return context()


@func
def nested_resolve_func() -> int:
    return add(1, 2).resolve()


@func
def add_to_resource(x: int, r: FakeExternalResource) -> int:
    return x + r.use_resource()


@func
def custom_resource_pipeline() -> int:
    """42 + 1 + 101 = 144"""
    with FakeExternalResource(some_field=42) as r1:
        value = add_to_resource(1, r1)
    with FakeExternalResource(some_field=101) as r2:
        value = add_to_resource(value, r2)
    return value


def test_silent_resolver():
    assert SilentResolver().resolve(pipeline(3, 5)) == 24


def test_silent_resolver_context():
    future = context_pipeline()
    result = SilentResolver().resolve(future)
    assert result.root_id == future.id
    assert result.run_id != future.id
    assert result.private.resolver_class() is SilentResolver

    future = direct_context_func()
    result = SilentResolver().resolve(future)
    assert result.root_id == future.id
    assert result.run_id == future.id


def test_nested_resolve():
    with pytest.raises(ResolutionError):
        SilentResolver().resolve(nested_resolve_func())


_tried = 0


class SomeException(Exception):
    pass


@func(retry=RetrySettings(exceptions=(SomeException,), retries=3))
def retry_three_times():
    global _tried
    _tried += 1
    raise SomeException()


def test_retry():
    future = retry_three_times()

    with pytest.raises(ResolutionError) as exc_info:
        SilentResolver().resolve(future)

    assert isinstance(exc_info.value.__context__, CalculatorError)
    assert isinstance(exc_info.value.__context__.__context__, SomeException)
    assert future.props.retry_settings.retry_count == 3
    assert future.state == FutureState.FAILED
    assert _tried == 4


def test_custom_resources():
    FakeExternalResource.reset_history()
    result = custom_resource_pipeline().resolve(SilentResolver())
    assert result == 144
    ids = FakeExternalResource.all_resource_ids()
    assert len(ids) == 2
    resource_history = FakeExternalResource.history_by_id(ids[0])
    state_history = [r.status.state for r in resource_history]
    expected_state_history = [
        ResourceState.CREATED,
        ResourceState.ACTIVATING,
        ResourceState.ACTIVE,
        ResourceState.DEACTIVATING,
        ResourceState.DEACTIVATED,
    ]
    assert state_history == expected_state_history

    resource_history = FakeExternalResource.history_by_id(ids[1])
    state_history = [r.status.state for r in resource_history]
    expected_state_history = [
        ResourceState.CREATED,
        ResourceState.ACTIVATING,
        ResourceState.ACTIVE,
        ResourceState.DEACTIVATING,
        ResourceState.DEACTIVATED,
    ]
    assert state_history == expected_state_history

    full_history = FakeExternalResource.history_by_id(None)
    first_resource_created_at_index, first_resource_id = next(
        (i, r.id)
        for i, r in enumerate(full_history)
        if r.status.state == ResourceState.CREATED
    )
    second_resource_created_at_index, second_resource_id = next(
        (i, r.id)
        for i, r in enumerate(full_history)
        if r.status.state == ResourceState.CREATED and r.id != first_resource_id
    )
    first_resource_activating_index = next(
        i
        for i, r in enumerate(full_history)
        if r.id == first_resource_id and r.status.state == ResourceState.ACTIVATING
    )

    # All resources should be created before any are activated since
    # they are created during execution of the outer func, but
    # are only activated once the func they're used in gets scheduled
    assert second_resource_created_at_index < first_resource_activating_index

    first_resource_deactivated_index = next(
        i
        for i, r in enumerate(full_history)
        if r.id == first_resource_id and r.status.state == ResourceState.DEACTIVATED
    )
    second_resource_activating_index = next(
        i
        for i, r in enumerate(full_history)
        if r.id == second_resource_id and r.status.state == ResourceState.DEACTIVATED
    )

    # The first resource should be deactivated before the second is activated
    assert first_resource_deactivated_index < second_resource_activating_index

    # SilentResolver should use local activation
    assert "_do_activate(True)" in FakeExternalResource.call_history_by_id(
        first_resource_id
    )
    assert "_do_activate(True)" in FakeExternalResource.call_history_by_id(
        second_resource_id
    )
