# Function Output Artifact Caching

<!-- ⚠️ **This design is invalidated by PR:**
[#[my_pr_number]](https://github.com/sematic-ai/sematic/pull/[my_pr_number]) -->

This design proposes an API and feature set to support Sematic function
caching, by marking which individual functions' outputs should be cached,
inside a specific caching namespace specified at the Resolver-level. The cached
values will be invalidated when changing the caching namespace, when changing
the input values, or, if explicitly stated, when changing the contents of the
source code.

**Addressed issue:** [#338](https://github.com/sematic-ai/sematic/issues/338).

**Accepted on:** 12/05/22

**Post-acceptance updates:**
N/A

## In Scope

- A minimal design that is supposed to be simple to use and which can be easily
  enhanced in the future based on user requests.
- A mechanism which allows caching and reuse of specific funcs' output between
  `Resolution`s and pipelines.
- A mechanism for specifying caching namespaces, and an explicit stock
  mechanism for invalidating the cache based on code changes.

## Out of Scope

- Explicit user-triggered cache invalidation.
- Browsing the cached values using a CLI tool or the UI.
- Implicit invalidation of the cache based on code changes, dependency changes,
  or container image changes.
- Preemptive deduplication of concurrent invocations of the same func with the
  same input parameters.

## Proposed External API

The `@func` decorator will expose a new `cache` boolean parameter which will
enable or disable caching for that function. By default this will be False.

The `LocalResolver` and `CloudResolver` init functions will be expose a new
`cache_namespace` string or callable parameter which will act as the cache key
namespace in which all executed funcs' outputs will be cached, as long as they
also have the `cache` flag activated. By default this will not be set.

The `Future` returned by invoking any func will be configurable with the
`cache_namespace`, which will be set by the Resolver, if not already set by the
developer.

API changes to `calculator.py`:

``` diff
    def func(
        func: Optional[Callable] = None,
        inline: bool = True,
+       cache: bool = False,
        resource_requirements: Optional[ResourceRequirements] = None,
        retry: Optional[RetrySettings] = None,
        base_image_tag: Optional[str] = None,
    ) -> Union[Callable, Calculator]:
        """
        Sematic Function decorator.
        Parameters
        ----------
        [...]
+       cache: bool
+           Whether to cache this func's output value under the `cache_namespace`
+           set on a Future in this func's ancestor chain. Do not activate this on a
+           non-deterministic function! Defaults to False.
        [...]
        """
```

API changes to `local_resolver.py` (and similar changes to `cloud_resolver.py`):

```diff
class LocalResolver(SilentResolver):
    """
    [...]
    Parameters
    ----------
    [...]
+   cache_namespace: Union[Callable[None, str], str]
+       A string or a Callable which returns a string, which will be used as
+       the cache key namespace in which this the funcs's outputs will be
+       cached, as long as they also have the `cache` flag activated.
    [...]

    def __init__(self,
        rerun_from: Optional[str] = None,
+       cache_namespace: Union[Callable[None, str], str] = None,
        **kwargs
    ):
        [...]
```

API changes to `future.py`:

```diff
    def set(self, **kwargs):
        """
        Set future properties: `name`, `cache_namespace`, `tags`.

        Parameters
        ----------
        [...]
+       cache_namespace: Union[Callable[None, str], str]
+           A string or a Callable which returns a string, which will be used as
+           the cache key namespace in which this func's output and any nested
+           funcs' outputs will be cached, as long as they also have the `cache`
+           flag activated.
        [...]
        """
```

## Example Usage

```python

@func(cache=True)
def my_func(a: int, b: int) -> int:
    return a + b

@func
def my_pipeline([...]) -> [...]:
    [...]
    x = my_func(a, b)
    y = my_func(c, d)
    [...]

@func
def my_other_pipeline([...]) -> [...]:
    [...]
    x = my_func(a, b)
    y = my_func(c, d)
    [...]

my_pipeline1 = my_pipeline([...]).set(
    name="example pipeline",
    tags=["example", "cached"],
).resolve(CloudResolver([...], cache_namespace="cache namespace 1"))

my_pipeline2 = my_pipeline([...]).set(
    name="example pipeline",
    tags=["example", "cached"],
).resolve(CloudResolver([...], cache_namespace=lambda () -> "cache namespace 2"))

my_pipeline3 = my_pipeline([...]).set(
    name="example pipeline",
    tags=["example", "cached"],
).resolve(CloudResolver([...], cache_namespace=lambda () -> "cache namespace 2"))

my_pipeline4 = my_pipeline([...]).set(
    name="example pipeline",
    tags=["example", "cached"],
).resolve(CloudResolver([...]))

my_other_pipeline1 = my_other_pipeline1([...]).set(
    name="other example pipeline",
    tags=["example", "cached"],
).resolve(CloudResolver([...], cache_namespace="cache namespace 1"))

```

When `my_pipeline1` is executed, `x` and `y`'s values are calculated from
scratch and cached in the "cache namespace 1" namespace.
When `my_pipeline2` is executed, `x` and `y`'s values are still calculated from
scratch, because they pertain to the separate "cache namespace 2" namespace,
and these values will be cached in that namespace.
When `my_pipeline3` is executed, `x` and `y` are not recalculated, because
their values are found in the "cache namespace 2" cache.
When `my_pipeline4` is executed, `x` and `y`'s values are calculated from
scratch, because although their `my_func` func is configured to activate the
cache, no `cache_namespace` is configured anywhere on the pipeline.
When `my_other_pipeline1` is executed, `x` and `y` are not recalculated,
because their values are found in the "cache namespace 1" cache, even though it
is executing a different pipeline than the one that initially populated the
cache.

## Git SHA-based Caching Namespace

The `cache_namespace` will take either a string, or a Callable which produces a
string. We will provide a stock Callable implementation which will use the
local Git SHA (together with configurable salts) in order to have a handy way
of invalidating the cache on code changes.

## Implementation Details

A cache namespace cannot be the final cache key under which an output
`Artifact` will be cached, so it is named accordingly. The actual hit / miss
decision for a func's execution also has to be made based on:
- the identity of the func itself - in order to differentiate between nested
  funcs' in a pipeline configured with a cache namespace
- on the contents of its inputs - in order to invalidate the cache for
  different invocations of a func with different input parameters.

Therefore, the actual cache key which will be used will be a hash over:
- the developer-specified cache namespace
- the func's module path and name
- a hash over the func's effective input argument dict
- a hash over the func's output type

I/O `Artifact`s are already saved in the database. Because the same `Artifact`
(same byte contents) can be produced by different funcs or by the same func
with different effective outputs, the `cache_key` cannot be directly associated
with an `Artifact`. Instead, the `cache_key` will be added as a field on the
`Run`. When executing a `Future` whose func is enabled for caching, and which
has a cache namespace configured on it, that `Future`'s resulting cache key
will be searched in the database.

In case of a miss, the `Future` will be invoked, and its output value will be
saved as an `Artifact` with the cache key in question.

In case of a hit, the `Future` will be marked as resolved without actually
invoking it, and this Future's sub-pipeline will be cloned, just like in the
"Rerun-from-here" feature, with its output value set to the `Artifact` which
determined the hit. The UI will mark this Run and any nested Runs as sourced
from the cache. This UI mark should be added to the rerun-from-here feature as
well.

## Future Work

- This is a minimal design that is supposed to be simple to use and which can
  be easily enhanced in the future based on user requests. Therefore, future
  changes might modify the computed final cache key. This will result in one
  cache miss for each cached func, which is acceptable behavior moving forward.
