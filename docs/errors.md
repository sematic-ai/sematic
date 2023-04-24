# Errors

## Only Standalone Functions can have resource requirements

```
ValueError: Only Standalone Functions can have resource requirements.
Try using @sematic.func(standalone=True, ...).
See https://go.sematic.dev/t3mynx.
```

In order for a Function to have its own dedicated resources, it needs to be a
[Standalone Function](./glossary.md#standalone-inline-function), i.e. run in its
own dedicated container.

```python
@sematic.func(standalone=True, resource_requirements=RESOURCE_REQS)
def foo():
    ...
```

Note that this only works with the
[`CloudResolver`](./glossary.md#cloud-execution).