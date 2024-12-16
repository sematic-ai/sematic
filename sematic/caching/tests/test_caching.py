# Standard Library
from typing import Dict
from unittest import mock

# Third-party
import pytest

# Sematic
from sematic import func
from sematic.abstract_future import AbstractFuture
from sematic.caching.caching import determine_cache_namespace, get_future_cache_key
from sematic.runners.state_machine_runner import StateMachineRunner


# these values were calculated by hand on paper to validate the algorithm
# (they were all correct on the first try)
MY_CACHE_KEY = "ec8eaec9ea3bd0315d5bd0839380ed2cab6bf526_my_namespace"
MY_OTHER_CACHE_KEY = "ec8eaec9ea3bd0315d5bd0839380ed2cab6bf526_my_other_namespace"


@func
def my_pipeline(a: int, b: Dict[str, int]) -> int:
    # a dict arg must be included ^ to check that we correctly cover
    # potential "TypeError: unhashable type" errors
    return a + b["test_key"]


@func
def my_other_pipeline(a: int) -> int:
    return a


def my_namespace(_: AbstractFuture) -> str:
    return "my_namespace"


def my_other_namespace(_: AbstractFuture) -> str:
    return "my_other_namespace"


@pytest.fixture(scope="function")
def my_future() -> AbstractFuture:
    future = my_pipeline(1, {"test_key": 2})
    future.resolved_kwargs = StateMachineRunner._get_concrete_kwargs(future)
    return future


@pytest.fixture(scope="function")
def my_other_future() -> AbstractFuture:
    future = my_other_pipeline(1)
    future.resolved_kwargs = StateMachineRunner._get_concrete_kwargs(future)
    return future


def test_none_namespace(my_future: AbstractFuture):
    with pytest.raises(ValueError, match="cannot be None"):
        get_future_cache_key(None, my_future)  # type: ignore


def test_unresolved_args_namespace():
    with pytest.raises(ValueError, match="Not all input arguments are resolved"):
        get_future_cache_key("my_namespace", my_pipeline(1, {"test_key": 2}))


def test_namespace_str_happy_path(my_future: AbstractFuture):
    actual = get_future_cache_key("my_namespace", my_future)
    assert actual == MY_CACHE_KEY

    actual = get_future_cache_key("my_other_namespace", my_future)
    assert actual == MY_OTHER_CACHE_KEY


def test_resolve_namespace_str_happy_path(my_future: AbstractFuture):
    actual = determine_cache_namespace("my_namespace", my_future)
    assert actual == "my_namespace"


def test_resolve_namespace_callable_happy_path(my_future: AbstractFuture):
    actual = determine_cache_namespace(my_namespace, my_future)
    assert actual == "my_namespace"

    actual = determine_cache_namespace(my_other_namespace, my_future)
    assert actual == "my_other_namespace"


def test_resolve_namespace_str_truncated(my_future: AbstractFuture):
    actual = determine_cache_namespace(
        "01234567890123456789012345678901234567890123456789extra",
        my_future,
    )
    assert actual == "01234567890123456789012345678901234567890123456789"


def test_resolve_namespace_callable_truncated(my_future: AbstractFuture):
    def my_custom_namespace(_: AbstractFuture) -> str:
        return "01234567890123456789012345678901234567890123456789extra"

    actual = determine_cache_namespace(my_custom_namespace, my_future)
    assert actual == "01234567890123456789012345678901234567890123456789"


def test_custom_resolve_namespace(
    my_future: AbstractFuture, my_other_future: AbstractFuture
):
    def my_custom_namespace(future: AbstractFuture) -> str:
        fqpn = future.function.get_func_fqpn()  # type: ignore # noqa: ignore

        if fqpn == "sematic.caching.tests.test_caching.my_pipeline":
            return "my_namespace"

        if fqpn == "sematic.caching.tests.test_caching.my_other_pipeline":
            return "my_other_namespace"

        return "whatever"

    actual = determine_cache_namespace(my_custom_namespace, my_future)
    assert actual == "my_namespace"

    actual = determine_cache_namespace(my_custom_namespace, my_other_future)
    assert actual == "my_other_namespace"


def test_invalid_args_resolve_namespace(my_future: AbstractFuture):
    with pytest.raises(ValueError, match="cannot be None"):
        determine_cache_namespace(None, my_future)

    actual = determine_cache_namespace("my_namespace", None)  # type: ignore
    assert actual == "my_namespace"

    with pytest.raises(ValueError, match="cannot be None"):
        determine_cache_namespace(my_namespace, None)  # type: ignore

    nested_future = mock.MagicMock()
    nested_future.is_root_future.return_value = False
    with pytest.raises(ValueError, match="must be a pipeline run root Future"):
        determine_cache_namespace(my_namespace, nested_future)


def test_malformed_resolve_namespace(my_future: AbstractFuture):
    def my_malformed_namespace() -> str:
        return "my_namespace"

    with pytest.raises(TypeError, match="takes 0 positional arguments but 1 was given"):
        determine_cache_namespace(my_malformed_namespace, my_future)  # type: ignore


def test_resolve_namespace_error_raised(my_future: AbstractFuture):
    def my_error_namespace(_: AbstractFuture) -> str:
        raise ValueError("test error")

    with pytest.raises(ValueError, match="test error"):
        determine_cache_namespace(my_error_namespace, my_future)
