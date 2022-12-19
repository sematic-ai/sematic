# Standard Library
from typing import Dict
from unittest import mock

# Third-party
import pytest

# Sematic
from sematic import func
from sematic.abstract_future import AbstractFuture
from sematic.caching.caching import get_future_cache_key, resolve_cache_namespace

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


def test_none_namespace():
    with pytest.raises(ValueError, match="cannot be None"):
        get_future_cache_key(None, my_pipeline(1, {"test_key": 2}))


def test_namespace_str_happy_path():
    actual = get_future_cache_key("my_namespace", my_pipeline(1, {"test_key": 2}))
    assert actual == MY_CACHE_KEY

    actual = get_future_cache_key("my_other_namespace", my_pipeline(1, {"test_key": 2}))
    assert actual == MY_OTHER_CACHE_KEY


def test_resolve_namespace_str_happy_path():
    actual = resolve_cache_namespace("my_namespace", my_pipeline(1, {"test_key": 2}))
    assert actual == "my_namespace"


def test_resolve_namespace_callable_happy_path():
    actual = resolve_cache_namespace(my_namespace, my_pipeline(1, {"test_key": 2}))
    assert actual == "my_namespace"

    actual = resolve_cache_namespace(
        my_other_namespace, my_pipeline(1, {"test_key": 2})
    )
    assert actual == "my_other_namespace"


def test_resolve_namespace_str_truncated():
    actual = resolve_cache_namespace(
        "01234567890123456789012345678901234567890123456789extra",
        my_pipeline(1, {"test_key": 2}),
    )
    assert actual == "01234567890123456789012345678901234567890123456789"


def test_resolve_namespace_callable_truncated():
    def my_custom_namespace(_: AbstractFuture) -> str:
        return "01234567890123456789012345678901234567890123456789extra"

    actual = resolve_cache_namespace(
        my_custom_namespace, my_pipeline(1, {"test_key": 2})
    )
    assert actual == "01234567890123456789012345678901234567890123456789"


def test_custom_resolve_namespace():
    def my_custom_namespace(future: AbstractFuture) -> str:
        fqpn = future.calculator.get_func_fqpn()  # type: ignore # noqa: ignore

        if fqpn == "sematic.caching.tests.test_caching.my_pipeline":
            return "my_namespace"

        if fqpn == "sematic.caching.tests.test_caching.my_other_pipeline":
            return "my_other_namespace"

        return "whatever"

    actual = resolve_cache_namespace(
        my_custom_namespace, my_pipeline(1, {"test_key": 2})
    )
    assert actual == "my_namespace"

    actual = resolve_cache_namespace(my_custom_namespace, my_other_pipeline(1))
    assert actual == "my_other_namespace"


def test_invalid_args_resolve_namespace():
    with pytest.raises(ValueError, match="cannot be None"):
        resolve_cache_namespace(None, my_pipeline(1, {"test_key": 2}))

    actual = resolve_cache_namespace("my_namespace", None)
    assert actual == "my_namespace"

    with pytest.raises(ValueError, match="cannot be None"):
        resolve_cache_namespace(my_namespace, None)

    nested_future = mock.MagicMock()
    nested_future.is_root_future.return_value = False
    with pytest.raises(ValueError, match="must be a Resolution root Future"):
        resolve_cache_namespace(my_namespace, nested_future)


def test_malformed_resolve_namespace():
    def my_malformed_namespace() -> str:
        return "my_namespace"

    with pytest.raises(TypeError, match="takes 0 positional arguments but 1 was given"):
        resolve_cache_namespace(my_malformed_namespace, my_pipeline(1, {"test_key": 2}))


def test_resolve_namespace_error_raised():
    def my_error_namespace(_: AbstractFuture) -> str:
        raise ValueError("test error")

    with pytest.raises(ValueError, match="test error"):
        resolve_cache_namespace(my_error_namespace, my_pipeline(1, {"test_key": 2}))
