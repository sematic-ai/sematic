## Inline Functions cannot have resource requirements

```
ValueError: Inline Functions cannot have resource requirements.
Try using @sematic.func(standalone=True, ...).
See https://go.sematic.dev/t3mynx.
```

[Inline Function](./glossary.md#standalone-inline-function)s run within the same
process and container as the `CloudResolver` orchestrating the pipeline.
Therefore, they cannot have custom resource requirements.

To use custom resource requirements, make the the Function "Standalone", i.e.
running in its own container:

```python
@sematic.func(standalone=True, resource_requirements=RESOURCE_REQS)
def foo():
    ...
```