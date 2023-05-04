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

## Your RayClusterConfig would require autoscaling

```
ValueError: Your RayClusterConfig would require autoscaling, but no 
AutoScalerConfig is provided. For more see: https://go.sematic.dev/KMzMCm
```

Your `RayClusterConfig` would require autoscaling, but no [`AutoScalerConfig`](https://docs.sematic.dev/integrations/ray#autoscalerconfig) is
provided. This means one of your scaling groups has a min number of
workers which differ from its max number of workers. See Sematic's
[Ray docs](https://docs.sematic.dev/integrations/ray#autoscalerconfig)
for more information about how to configure the `AutoScalerConfig`.
Note that the autoscaler will execute in the same Kubernetes pod as
the Ray head, so you must have a Kubernetes node available which can
accomodate the resources for the head PLUS the autoscaler.
