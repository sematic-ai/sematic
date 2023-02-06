## Caching Func Runs

If you have deterministic functions which take the exact same inputs between
[Resolutions](glossary.md#resolution) and whose executions take a lot of time
or resources to complete, such as data pre-processing, then you can mark those
functions for caching, under a specific caching namespace.

On every invocation of a function marked in this way, Sematic checks if that
function had been already invoked in the past with the same effective input
values. If so, the resulting output [Artifact](glossary.md#artifact) from that
original [Run](glossary.md#run) is directly used as this new invocation's
output. This means that any potential functions nested under this function will
not be invoked either. If no prior run matches, the function is executed as
usual.

These cached Artifacts can be grouped together under a specific cache
namespace, in order to manage the caching behavior between different pipelines
that reuse the same cached funcs, or to  invalidate the cache. this namespace
can either be a string, or a `Callable` which takes as input the root
[Future](glossary.md#future) and returns a string. This `Callable` will be
executed immediately after the Resolution starts.

In order to enable this behavior:

- Enable the cache flag on the function definition:
    ```python
    @sematic.func(cache=True)
    def my_function([...]) -> [...]:
      [...]
    ```

- Instantiate the [Resolver](glossary.md#resolvers) with a cache namespace:
    ```python
    my_pipeline([...]).resolve(CloudResolver(cache_namespace="my namespace"))
    ```

## Context

Sometimes you may want to record the results of an execution with
a third party or custom tool. In this case, you would want to
preserve the ability to reference the Sematic run that the results
came from. Sematic provides an API you can use to do this directly
within your Sematic funcs:

```python
import sematic

@sematic.func
def add(a: int, b: int) -> int:
    result = a + b

    # track this run's results with some hypothetical
    # experiment management tool.
    some_experiment_manager().record_result(
        sematic.context().run_id, {
            "a": a,
            "b": b,
            "result": result,
        }
    )
    return result
```

The context object returned by `sematic.context()` contains both the `run_id` for the
execution of the current func, as well as the run id for the root run of the pipeline
currently being executed (in `root_id`).
