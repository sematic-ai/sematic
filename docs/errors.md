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
[`CloudRunner`](./glossary.md#cloud-execution).

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

## cannot open shared object file

```
OSError: libcublas.so.11: cannot open shared object file: No such file or directory
```

Cuda shared libraries can't be found. There are two possible fixes for this:

(1) Ensure that the required Cuda libraries are installed in your base docker image and
in your development environment, and ensure that the location where they are installed
are on the image's (and your dev environment's) `LD_LIBRARY_PATH`
(2) Ensure that you have pytorch 1.30 or greater in your dependencies, and import
`sematic.torch_patch` before you import pytorch (or anything that imports pytorch
transitively). 

Solution (1) is preferred if you are not using bazel, but will work even if you are using
bazel. Solution (2) is preferred if you are using bazel, and will not work if you are
not using bazel.

## 413 Request Entity Too Large

```
2023-08-28 11:20:41,960  [ERROR] sematic.api_client: Server returned 413 for PUT https://josh.dev-usw2-sematic0.sematic.cloud/api/v1/graph: <html>
<head><title>413 Request Entity Too Large</title></head>
<body>
<center><h1>413 Request Entity Too Large</h1></center>
<hr><center>nginx</center>
</body>
</html>
sematic.api_client.BadRequestError: The PUT request to https://example.url.cloud/api/v1/graph was invalid, response was 413.
Please check the Sematic Server logs for more information. You may search the server logs for request id '09e9d9b4d'
```

This usually indicates that one of your artifacts (aka function inputs/outputs) are too large.
Consider finding a way to reduce their size.