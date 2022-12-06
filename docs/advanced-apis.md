# Advanced APIs

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

## Resource APIs
Coming soon...