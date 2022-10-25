# Standard Library
import typing
from functools import wraps


def memoized_property(fget: typing.Callable) -> property:
    """
    Type-hinted version of https://github.com/estebistec/python-memoized-property

    Return a property attribute for new-style classes that only calls
    its getter on the first access. The result is stored and on subsequent
    accesses is returned, preventing the need to call the getter any more.

    Example
    -------
    >>> class C(object):
    ...     load_name_count = 0
    ...     @memoized_property
    ...     def name(self):
    ...         "name's docstring"
    ...         self.load_name_count += 1
    ...         return "the name"
    >>> c = C()
    >>> c.load_name_count
    0
    >>> c.name
    "the name"
    >>> c.load_name_count
    1
    >>> c.name
    "the name"
    >>> c.load_name_count
    1
    """
    cache_name = _make_cache_name(fget.__name__)

    @wraps(fget)
    def fget_memoized(self):
        if not hasattr(self, cache_name):
            setattr(self, cache_name, fget(self))
        return getattr(self, cache_name)

    fget_memoized.__annotations__ = fget.__annotations__

    return property(fget_memoized)


def _make_cache_name(name: str):
    return f"_{name}"


def memoized_indexed(fget: typing.Callable) -> typing.Callable:
    """
    Memoizes the output of methods with a single string argument (index).

    Example
    -------
    >>> class C(object):
    ...     load_name_count = defaultdict(lambda: 0)
    ...     @memoized_indexed
    ...     def name_by_user_id(self, user_id: str) -> str:
    ...         self.load_name_count[user_id] += 1
    ...         return self._name_mapping[user_id]
    >>> c = C()
    >>> c.load_name_count
    {}
    >>> c.name_by_user_id("abc123")
    "abc123's name"
    >>> c.load_name_count
    {"abc123": 1}
    >>> c.name_by_user_id("abc123")
    "abc123's name"
    >>> c.load_name_count
    {"abc123": 1}
    """
    cache_name = _make_cache_name(fget.__name__)

    @wraps(fget)
    def fget_memoized(self, index: str):
        cache = getattr(self, cache_name, {})
        setattr(self, cache_name, cache)

        if index not in cache:
            cache[index] = fget(self, index)

        return cache[index]

    fget_memoized.__annotations__ = fget.__annotations__

    return fget_memoized
