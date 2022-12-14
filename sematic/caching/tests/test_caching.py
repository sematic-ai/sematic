# Standard Library
from typing import Dict

# Third-party
import pytest

# Sematic
from sematic import func
from sematic.abstract_future import AbstractFuture
from sematic.caching.caching import _hash, get_future_cache_key

# these values were calculated by hand on paper to validate the algorithm
# (they were all correct on the first try)
HASH_1 = "356a192b7913b04c54574d18c28d46e6395428ab"
HASH_A = "86f7e437faa5a7fce15d1ddcb9eaeaea377667b8"
MY_NAMESPACE_CACHE_KEY = "512706a76ddb96c9992c690a14a44a0ff733462f"
MY_OTHER_NAMESPACE_CACHE_KEY = "b7de1f83e736134df188d99683f450a45c611e19"
MY_CUSTOM_OTHER_NAMESPACE_CACHE_KEY = "de9cc62d0da2c5822048959687e7eacd72c287a0"


@func
def my_pipeline(a: int, b: Dict[str, int]) -> int:
    # a dict arg must be included ^ to check that we correctly cover
    # potential "TypeError: unhashable type" errors
    return a + b["test_key"]


@func
def my_other_pipeline(a: int) -> int:
    return a


def test_hash():
    assert _hash(1) == HASH_1
    assert _hash("a") == HASH_A


def test_none_namespace():
    with pytest.raises(ValueError, match="cannot be None"):
        get_future_cache_key(None, my_pipeline(1, {"test_key": 2}))


def test_str_namespace_happy_path():
    actual = get_future_cache_key("my_namespace", my_pipeline(1, {"test_key": 2}))
    assert actual == MY_NAMESPACE_CACHE_KEY

    actual = get_future_cache_key("my_other_namespace", my_pipeline(1, {"test_key": 2}))
    assert actual == MY_OTHER_NAMESPACE_CACHE_KEY


def test_callable_namespace_happy_path():
    def my_namespace(_: AbstractFuture) -> str:
        return "my_namespace"

    actual = get_future_cache_key(my_namespace, my_pipeline(1, {"test_key": 2}))
    assert actual == MY_NAMESPACE_CACHE_KEY

    def my_other_namespace(_: AbstractFuture) -> str:
        return "my_other_namespace"

    actual = get_future_cache_key(my_other_namespace, my_pipeline(1, {"test_key": 2}))
    assert actual == MY_OTHER_NAMESPACE_CACHE_KEY


def test_custom_callable_namespace():
    def my_custom_namespace(future: AbstractFuture) -> str:
        fqpn = future.calculator.get_func_fqpn()  # type: ignore # noqa: ignore

        if fqpn == "sematic.caching.tests.test_caching.my_pipeline":
            return "my_namespace"

        if fqpn == "sematic.caching.tests.test_caching.my_other_pipeline":
            return "my_other_namespace"

        return "whatever"

    actual = get_future_cache_key(my_custom_namespace, my_pipeline(1, {"test_key": 2}))
    assert actual == MY_NAMESPACE_CACHE_KEY

    actual = get_future_cache_key(my_custom_namespace, my_other_pipeline(1))
    assert actual == MY_CUSTOM_OTHER_NAMESPACE_CACHE_KEY


def test_malformed_callable_namespace():
    def my_namespace() -> str:
        return "my_namespace"

    with pytest.raises(TypeError, match="takes 0 positional arguments but 1 was given"):
        get_future_cache_key(my_namespace, my_pipeline(1, {"test_key": 2}))


def test_callable_namespace_failure_handled():
    def my_namespace(_: AbstractFuture) -> str:
        raise ValueError("test error")

    with pytest.raises(ValueError, match="test error"):
        get_future_cache_key(my_namespace, my_pipeline(1, {"test_key": 2}))
