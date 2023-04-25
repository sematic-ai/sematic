# Standard Library
import time

# Third-party
import pytest

# Sematic
from sematic.abstract_calculator import CalculatorError
from sematic.abstract_future import FutureState
from sematic.calculator import func
from sematic.future_context import PrivateContext, SematicContext, context, set_context
from sematic.plugins.abstract_external_resource import ResourceState
from sematic.resolvers.silent_resolver import SilentResolver
from sematic.resolvers.tests.fixtures import FakeExternalResource
from sematic.retry_settings import RetrySettings
from sematic.tests.utils import RUN_SLOW_TESTS
from sematic.utils.exceptions import (
    ExternalResourceError,
    ResolutionError,
    TimeoutError,
)


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
    # If you don't use SilentResolver() here, the test process
    # takes MUCH longer to complete
    return add(1, 2).resolve(SilentResolver())


@func
def custom_resource_func() -> int:
    """42 + 1 + 101 = 144"""
    with FakeExternalResource(some_field=42) as r1:
        value = 1 + r1.use_resource()
    with FakeExternalResource(some_field=101) as r2:
        value = value + r2.use_resource()
    return value


@func
def do_sleep(seconds: float) -> float:
    time.sleep(seconds)
    return 42


@func
def nested_sleep(seconds: float, ignored: float = 0.0) -> float:
    return do_sleep(seconds)


@func
def timeout_pipeline(long_child: bool, long_grandchild: bool) -> int:
    partial = do_sleep(120.0 if long_child else 0).set(timeout_mins=1)
    return nested_sleep(120.0 if long_grandchild else 0, partial).set(timeout_mins=1)


def test_silent_resolver():
    assert SilentResolver().resolve(pipeline(3, 5)) == 24


def test_silent_resolver_context():
    future = context_pipeline()
    result = SilentResolver().resolve(future)
    assert result.root_id == future.id
    assert result.run_id != future.id
    assert result.private.load_resolver_class() is SilentResolver

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
    result = custom_resource_func().resolve(SilentResolver())
    assert result == 144
    ids = FakeExternalResource.all_resource_ids()
    assert len(ids) == 2
    state_history = FakeExternalResource.state_history_by_id(ids[0])
    expected_state_history = [
        ResourceState.CREATED,
        ResourceState.ACTIVATING,
        ResourceState.ACTIVE,
        ResourceState.DEACTIVATING,
        ResourceState.DEACTIVATED,
    ]
    assert state_history == expected_state_history

    state_history = FakeExternalResource.state_history_by_id(ids[1])
    expected_state_history = [
        ResourceState.CREATED,
        ResourceState.ACTIVATING,
        ResourceState.ACTIVE,
        ResourceState.DEACTIVATING,
        ResourceState.DEACTIVATED,
    ]
    assert state_history == expected_state_history

    full_history = FakeExternalResource.history_by_id(None)
    first_resource_id = next(
        r.id for r in full_history if r.status.state == ResourceState.CREATED
    )
    second_resource_id = next(
        r.id
        for r in full_history
        if r.status.state == ResourceState.CREATED and r.id != first_resource_id
    )

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


def test_activate_resource_for_run():
    FakeExternalResource.reset_history()
    to_activate = FakeExternalResource()
    run_id = "abc123"
    root_id = "xyz789"
    activated = SilentResolver.activate_resource_for_run(to_activate, run_id, root_id)
    assert activated.status.state == ResourceState.ACTIVE

    stored = SilentResolver._resource_manager.get_resource_for_id(to_activate.id)
    assert stored == activated
    assert SilentResolver._resource_manager.resources_by_root_id(root_id) == [stored]


def test_activation_failures_for_resource():
    FakeExternalResource.reset_history()
    run_id = "abc1232"
    root_id = "xyz7892"
    with pytest.raises(ExternalResourceError, match=r".*Intentional fail.*"):
        with set_context(
            SematicContext(
                run_id=run_id,
                root_id=root_id,
                private=PrivateContext(resolver_class_path=SilentResolver.classpath()),
            )
        ):
            with FakeExternalResource(
                raise_on_activate=True, activation_timeout_seconds=0.1
            ):
                pass
    resources = SilentResolver._resource_manager.resources_by_root_id(root_id)
    assert len(resources) == 1
    stored = resources[0]
    assert stored.status.state == ResourceState.DEACTIVATED

    run_id = "abc1233"
    root_id = "xyz7893"
    with pytest.raises(ExternalResourceError, match=r"Timed out deactivating.*"):
        with set_context(
            SematicContext(
                run_id=run_id,
                root_id=root_id,
                private=PrivateContext(resolver_class_path=SilentResolver.classpath()),
            )
        ):
            with FakeExternalResource(
                raise_on_update=True,
                activation_timeout_seconds=0.1,
                deactivation_timeout_seconds=0.1,
            ):
                raise AssertionError("Should not reach here")
    resources = SilentResolver._resource_manager.resources_by_root_id(root_id)
    assert len(resources) == 1
    stored = resources[0]

    # not deactivated because the resolver failed to get an update
    # about the status while trying to deactivate
    assert stored.status.state == ResourceState.DEACTIVATING


def test_activation_timeout_for_resource():
    FakeExternalResource.reset_history()
    run_id = "abc1233"
    root_id = "xyz789111"
    with pytest.raises(ExternalResourceError, match=r"Timed out activating.*"):
        with set_context(
            SematicContext(
                run_id=run_id,
                root_id=root_id,
                private=PrivateContext(resolver_class_path=SilentResolver.classpath()),
            )
        ):
            started_activate = time.time()
            with FakeExternalResource(
                slow_activate=True, activation_timeout_seconds=0.0
            ):
                raise AssertionError("Should not reach here")
    exited_with_block = time.time()
    resources = SilentResolver._resource_manager.resources_by_root_id(root_id)
    assert len(resources) == 1
    assert exited_with_block - started_activate < 5


def test_deactivation_timeout_for_resource():
    FakeExternalResource.reset_history()
    run_id = "abc123334"
    root_id = "xyz789112"
    with pytest.raises(ExternalResourceError, match=r"Timed out deactivating.*"):
        with set_context(
            SematicContext(
                run_id=run_id,
                root_id=root_id,
                private=PrivateContext(resolver_class_path=SilentResolver.classpath()),
            )
        ):
            started_activate = time.time()
            with FakeExternalResource(
                slow_deactivate=True, deactivation_timeout_seconds=0.0
            ):
                raise AssertionError("Should not reach here")
    exited_with_block = time.time()
    resources = SilentResolver._resource_manager.resources_by_root_id(root_id)
    assert len(resources) == 1
    assert exited_with_block - started_activate < 5


def test_deactivation_failures_for_resource():
    FakeExternalResource.reset_history()
    run_id = "abc1234"
    root_id = "xyz7894"
    reached_inside_with_block = False
    with pytest.raises(
        ExternalResourceError, match=r"Could not deactivate.*Intentional fail.*"
    ):
        with set_context(
            SematicContext(
                run_id=run_id,
                root_id=root_id,
                private=PrivateContext(resolver_class_path=SilentResolver.classpath()),
            )
        ):
            with FakeExternalResource(
                raise_on_deactivate=True, deactivation_timeout_seconds=0.1
            ):
                reached_inside_with_block = True
    assert reached_inside_with_block
    resources = SilentResolver._resource_manager.resources_by_root_id(root_id)
    assert len(resources) == 1
    stored = resources[0]

    assert stored.status.state == ResourceState.ACTIVE


@pytest.mark.skipif(
    not RUN_SLOW_TESTS,
    reason="This test takes a long time to execute, and is disabled by default",
)
def test_timeout():
    result = timeout_pipeline(long_child=False, long_grandchild=False).resolve(
        SilentResolver()
    )
    assert result == 42.0

    future = timeout_pipeline(long_child=True, long_grandchild=False)
    error_text = None
    try:
        future.resolve(SilentResolver())
    except Exception as e:
        error_text = str(e)
    assert TimeoutError.__name__ in error_text

    future = timeout_pipeline(long_child=False, long_grandchild=True)
    error_text = None
    try:
        future.resolve(SilentResolver())
    except Exception as e:
        error_text = str(e)
    assert TimeoutError.__name__ in error_text

    future = do_sleep(120).set(timeout_mins=1)
    error_text = None
    try:
        future.resolve(SilentResolver())
    except Exception as e:
        error_text = str(e)
    assert TimeoutError.__name__ in error_text
