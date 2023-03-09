# Standard Library
import json
import logging
from typing import Callable, Optional, Union

# Sematic
from sematic.abstract_future import AbstractFuture
from sematic.types.serialization import (
    get_json_encodable_summary,
    type_to_json_encodable,
    value_to_json_encodable,
)
from sematic.utils.hashing import get_str_sha1_digest, get_value_and_type_sha1_digest

CACHE_NAMESPACE_MAX_LENGTH = 50

CacheNamespaceCallable = Callable[[AbstractFuture], str]
CacheNamespace = Optional[Union[str, CacheNamespaceCallable]]

logger = logging.getLogger(__name__)


def resolve_cache_namespace(
    cache_namespace: CacheNamespace, root_future: AbstractFuture
) -> str:
    """
    Returns a string cache namespace from a `CacheNamespace`, executing the `Callable`
    instances of this type, if it is the case.

    The string representation is truncated to 50 characters, in order to be a
    human-readable part of the final cache key for each `Future` execution.

    Parameters
    ----------
    cache_namespace: CacheNamespace
        A string or a `Callable` which returns a string, which is used as the cache key
        namespace.
    root_future: AbstractFuture
        The root Future of the pipeline for which to look up the code git commit status.

    Returns
    -------
    A string of maximum length 50.

    Raises
    ------
    ValueError:
        If `cache_namespace` is `None` or if `cache_namespace` is a `Callable` and
        `root_future` is not an actual root `Future`.
    """
    if cache_namespace is None:
        raise ValueError("`cache_namespace` cannot be None!")

    if isinstance(cache_namespace, str):
        return _truncate_namespace(cache_namespace)

    if root_future is None:
        raise ValueError("`root_future` cannot be None!")
    if not root_future.is_root_future():
        raise ValueError("`root_future` must be a Resolution root Future!")

    logger.debug("Calling cache_namespace %s", cache_namespace)

    # TODO: ponder async execution with a timeout
    namespace = str(cache_namespace(root_future))

    logger.debug(
        "Finished calling cache_namespace %s with result: %s",
        cache_namespace,
        namespace,
    )

    return _truncate_namespace(namespace)


def get_future_cache_key(cache_namespace: str, future: AbstractFuture) -> str:
    """
    Generates a cache key that can be used to uniquely identify the output value of a
    deterministic function.

    The cache key is under the form "<SHA1>_<cache_namespace>". The first part is a hash
    over the `Future` func fully qualified path name, its output type, and its effective
    input arguments names, types, and values. Consequently, modifying any of these between
    calls to the func will modify the resulting cache key, and result in a miss.

    Parameters
    ----------
    cache_namespace: str
        A string which is used as the cache key namespace.
    future: AbstractFuture
        The future for which to calculate the cache key.

    Returns
    -------
    A cache key string that can be used to uniquely identify the output value of a
    deterministic function. It is under the form "<SHA1>_<cache_namespace>".
    """
    # even if the type hint does not include Optional,
    # this code is critical and must be properly sanitized
    if cache_namespace is None:
        raise ValueError("`cache_namespace` cannot be None!")

    if len(future.kwargs) != len(future.resolved_kwargs):
        raise ValueError("Not all input arguments are resolved!")

    func_fqpn = future.calculator.get_func_fqpn()  # type: ignore
    output_type_repr = repr(future.calculator.output_type)
    input_args_hash = _get_input_args_hash(future)

    hash_base = f"{func_fqpn}|{output_type_repr}|{input_args_hash}"
    hashed_base = get_str_sha1_digest(hash_base)
    cache_key = f"{hashed_base}_{cache_namespace}"

    logger.debug("Generated cache key `%s` from base: %s", cache_key, hash_base)
    return cache_key


def _truncate_namespace(
    namespace: str, max_length: int = CACHE_NAMESPACE_MAX_LENGTH
) -> str:
    """
    Ensures that the namespace is right-truncated to the specified length, and logs a
    warning message if it was actually modified.
    """
    if len(namespace) <= max_length:
        return namespace

    namespace = namespace[:max_length]
    logger.warning(
        "Truncated the cache namespace to %s characters: %s", max_length, namespace
    )

    return namespace


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
    input_arg_hashes = {}
    for name, value in future.resolved_kwargs.items():

        type_ = future.calculator.input_types[name]
        type_serialization = type_to_json_encodable(type_)
        value_serialization = value_to_json_encodable(value, type_)
        json_summary, _ = get_json_encodable_summary(value, type_)

        hashed_value = get_value_and_type_sha1_digest(
            value_serialization, type_serialization, json_summary
        )
        input_arg_hashes[name] = hashed_value

    # we rely on the registered value serializers to provide
    # respective recursive deterministic sorted representations
    input_arg_hashes_dump = json.dumps(input_arg_hashes, sort_keys=True, default=str)
    logger.debug("Input arg hashes: %s", input_arg_hashes)

    return get_str_sha1_digest(input_arg_hashes_dump)
