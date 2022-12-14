# Standard Library
import hashlib
import json
import logging
from typing import Any, Callable, Optional, Union

# Sematic
from sematic.abstract_future import AbstractFuture
from sematic.types.serialization import value_to_json_encodable

CacheNamespaceCallable = Callable[[AbstractFuture], str]
CacheNamespace = Optional[Union[str, CacheNamespaceCallable]]

logger = logging.getLogger(__name__)


def get_future_cache_key(
    cache_namespace: CacheNamespace, future: AbstractFuture
) -> str:
    """
    Generates a cache key that can be used to uniquely identify the output value of a
    deterministic function.

    Parameters
    ----------
    cache_namespace: CacheNamespace
        A string or a `Callable` which returns a string, which is used as the cache key
        namespace.
    future: AbstractFuture
        The future for which to calculate the cache key.

    Returns
    -------
    A cache key string that can be used to uniquely identify the output value of a
    deterministic function.
    """
    # this may raise, so do it early
    cache_namespace = _resolve_namespace(cache_namespace=cache_namespace, future=future)

    func_fqpn = future.calculator.get_func_fqpn()  # type: ignore # noqa: ignore
    output_type_repr = repr(future.calculator.output_type)
    input_args_hash = _get_input_args_hash(future)

    hash_base = f"{cache_namespace}|{func_fqpn}|{output_type_repr}|{input_args_hash}"
    cache_key = _hash(hash_base)

    logger.debug("Generated cache key `%s` from base: %s", cache_key, hash_base)
    return cache_key


def _get_input_args_hash(future: AbstractFuture) -> str:
    # 1. we want to avoid constructing a large string containing all the serialized values
    # and then hashing that, because its memory footprint is potentially very large, and
    # because we would be duplicating memory usage between the individual value
    # representations and the concatenated result
    # 2. the consequence of applying the hash function multiple times is acceptable
    # 3. we also push the application of the hash to each respective serialized value in
    # order to avoid keeping references to the resulting strings, so that they can be
    # deallocated quickly
    # TODO #403: do these things in a sustainable and efficient way
    serialized_input_arg_tuples = []
    for name, value in future.kwargs.items():
        json_value = value_to_json_encodable(value, future.calculator.input_types[name])
        hashed_value = _hash(json.dumps(json_value, sort_keys=True))
        serialized_input_arg_tuples.append((name, hashed_value))

    # we rely on the registered value serializers to provide
    # respective recursive deterministic sorted representations
    return _hash(str(sorted(serialized_input_arg_tuples)))


def _resolve_namespace(cache_namespace: CacheNamespace, future: AbstractFuture) -> str:
    """
    Returns a string cache namespace from a `CacheNamespace`, executing the `Callable`
    instances of this type, if it is the case.
    """
    if cache_namespace is None:
        raise ValueError("`cache_namespace` cannot be None!")

    if isinstance(cache_namespace, str):
        return str(cache_namespace)

    logger.debug("Calling cache_namespace %s", cache_namespace)

    # TODO: ponder async execution with a timeout
    namespace = str(cache_namespace(future))

    logger.debug(
        "Finished calling cache_namespace %s with result: %s",
        cache_namespace,
        namespace,
    )

    return namespace


def _hash(value: Any) -> str:
    """
    Utility method for performing the actual hashing of a value.
    """
    # we don't need a cryptographic hash, but we do need a fast hash
    # unfortunately the builtin hash is initialized with a random salt seed on program
    # initialization, and this cannot be reset,
    # so we use sha1 for now
    # https://automationrhapsody.com/md5-sha-1-sha-256-sha-512-speed-performance/
    return hashlib.sha1(str(value).encode("utf-8")).hexdigest()
