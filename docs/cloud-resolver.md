In Sematic, resolvers implement different so-called "resolution" strategies. For
example, as described in [Local execution](./local-execution.md),
`LocalResolver` will resolve your pipeline graph and execute all steps on your local machine.

`CloudResolver` will resolve your pipeline graph in a Kubernetes cluster.

{% hint style="info" %}

### Prerequisite

In order to execute Sematic pipelines on a Kubernetes cluster, the API server
and web dashboard need to be deployed in said cluster. See [Deploy
Sematic](./deploy.md).

{% endhint %}

## `CloudResolver` usage

In order to use `CloudResolver`, simply pass an instance to your top-level
Sematic Function's `resolve` method:

```python
pipeline(...).resolve(CloudResolver())
```

This makes the assumption that a container image was built and registered with a
container registry. At this time, Sematic only supports Bazel as a way to build
and register Docker images at runtime. See [Container
images](./container-images.md).

{% hint style="info" %}

### Logging

By default, Sematic will ingest logs for remote runs and display them
in the dashboard. However, if you wish to have the logs from remote
executions go directly to the pod's stdout/stderr without Sematic
attempting to ingest them, you can configure the user setting
`SEMATIC_LOG_INGESTION_MODE=off`. Like all other user settings, this
can be overridden by environment variables.

{% endhint %}

## Execution on Kubernetes

Sematic will run two types of pods for each pipeline:

* **Driver pod** – this is where the graph of your pipeline gets processed, and
  where the `Resolver` and [Inline
  Functions](./glossary.md#standalone-inline-function) run. This pod has the
  word "driver" in its name.
* **Worker pods** – this is where [Standalone Functions](./glossary.md#standalone-inline-function)
  (`@sematic.func(standalone=True`). These pods have the word "worker" in their
  name.

By default, the execution of the graph and all [Sematic
Functions](./glossary.md#sematic-function) will run in a single pod, the
resolver pod. This is fine for minor pipeline steps that take up little time and
resources. Some Functions may require specific resources (e.g. GPUs) and
need to run in their own standalone containers. This can be achieved as follows:

```python
@sematic.func(standalone=True)
def train_model(...):
    ...
```

[Standalone Functions](./glossary.md#standalone-inline-function) will be
executed asynchronously as separate Kubernetes pods.

### Customize resource requirements

Sematic lets you customize what resources to allocate to particular pipeline
steps (Sematic Functions).

Pass a `ResourceRequirements` object to the Sematic decorator as follows:

```python
from sematic import ResourceRequirements, KubernetesResourceRequirements

GPU_RESOURCE_REQS = ResourceRequirements(
    kubernetes=KubernetesResourceRequirements(
        # Note: the kind of node selector options that are valid will depend on
        # your particular deployment of Kubernetes. Talk to the person who manages
        # your Kubernetes cluster if you think you might need this. It is primarily
        # useful in Sematic to gain access to nodes with GPUs.
        node_selector={"node.kubernetes.io/instance-type": "g4dn.xlarge"},

        # The resource requirements of the job. Information on the format of valid
        # values can be found here: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
        # the dictionary provided here will be used for both "limits" and "requests".
        requests={"cpu": "1", "memory": "1Gi"},

        # By default, Docker uses a 64MB /dev/shm partition. If this flag is set,
        # a memory-backed tmpfs that expands up to half of the available memory file
        # is used instead.
        mount_expanded_shared_memory=True,
    )
)

@sematic.func(standalone=True, resource_requirements=GPU_RESOURCE_REQS)
def train_model(...):
    ...
```

If there is a corresponding node available in your Kubernetes cluster, this
function will be executed on that node.

Note that `standalone=True` is necessary for these resource requirements to be
honored, otherwise, they will be ignored.

### Understanding Inline and Standalone Functions

Every Sematic func executes in one of two places:

(1) The driver container
(2) Its own, dedicated container

The *only* determining factor in which of these two is used for a given Function
is whether or not it has `standalone=True`. For functions where
`standalone=False` (the default), they will execute in the driver container.
This is best used for very lightweight functions that execute quickly and don't
make any calls to external services. For functions where `standalone=True`, they
execute in their own containers.

A common source of confusion with Inline Functions is to think there's a
relationship between nested functions and inline. Consider the following code:

```python
@sematic.func(standalone=True)
def calculate_average(a: float, b: float, c: float) -> float:
  total = add(a, b, c)
  average = divide(total, 3)

@sematic.func(standalone=True)
def add(a: float, b: float, c: float) -> float:
  return a + b + c

@sematic.func(standalone=False)
def divide(a: float, b: int) -> float:
  return a / b
```

Let's assume `calculate_average` and `add` are actually doing something
"heavy" that requires a dedicated container, rather than just performing
simple arithmetic operations.

People sometimes assume that since `divide` is nested inside
`calculate_average`, and `divide` is inline, `divide` must execute in the same
container as `calculate_average`. This is NOT correct. This misunderstanding
stems from a misunderstanding of how Sematic works with Futures. Recall that
[Sematic Functions](./glossary.md#sematic-function) return futures when you call
them (see [Future Algebra](future-algebra.md)). That means that `total` in
`calculate_average` *actually holds a Future instead of a `float`*. So when
`divide(total, 3)` is called above, the content of `total` is not even known.
Therefore, how could it be executed?

Instead, what happens is this:

1. `add` is called and immediately returns a Future without doing any work
2. `divide` is called, given the Future from `add` and the constant `3`. It
also returns immediately without doing any work.
3. `calculate_average` returns the `Future` output by `divide`
4. The driver job analyzes the `Future` coming from `calculate_average` and
sees that to get the value for it, it must first execute `add` and then
execute `divide`.
5. Since `add` is standalone, the driver starts a container within which to
execute `add`. `add` returns an actual `float` which is the sum of `a`, `b`, and
`c`.
6. The driver sees that it now has everything required to execute `divide`, so
it does so. Since `divide` is inline, the driver doesn't need to start a new
container for it, and instead it executes `divide` in its own process.

#### When to use Standalone or Inline?

- Any [Sematic Function](./glossary.md#sematic-function) doing something
"trivial" that executes in a few seconds or less and requires negligible CPU or
memory should be inline.
- Any [Sematic Functions](./glossary.md#sematic-function) which primarily calls
other Sematic functions and doesn't do any work "of its own" aside from these
calls should be inline.
- Any other [Sematic Functions](./glossary.md#sematic-function) should be
standalone. In practice this usually means "leaf node" Sematic functions that
don't call other Sematic functions and which do some "real work."

Most Sematic functions tend to meet the first two criteria, so functions are inline
by default.

#### Can I make nested functions execute in the parent container?

Let's suppose that you wanted `add` and `divide` to execute in the
same container as `calculate_average` above. Is that possible? Yes!
You can just remove the `@sematic.func` decorator from `add` and
`divide` to make them regular python functions. In this case, they will
execute just like any other python code--immediately at the time they
are called, in the same process as the code that called them. In this case,
Sematic will not track or visualize the functions.

### When to call `.resolve()`

Sometimes you will find yourself in the middle of a Sematic function
with a Future that you wish to use as a regular python object. Given
that calling `.resolve()` on a Future turns that `Future` into a
concrete value, you may be tempted to do the following:

```python
@sematic.func
def pipeline() -> int:
    # intermediate_result will hold a Future
    intermediate_result = nested_sematic_func()

    # DON'T DO THIS!!!
    return intermediate_result.resolve().some_method()
```

The reason you don't want to do this is that it will create an
entirely separate pipeline, rooted at the `nested_sematic_func` call
and independent of `pipeline`. In this case, `pipeline` will show up
in the UI as an empty pipeline, and all the work for `nested_sematic_func`
will happen in the container where `pipeline` executes. Instead, the way
to use `some_method()` on the python object that `nested_sematic_func`
produces is to use a wrapping sematic func:

```python
@sematic.func
def pipeline() -> int:
    # intermediate_result will hold a Future
    intermediate_result = nested_sematic_func()

    return call_some_method(intermediate_result)

@sematic.func
def call_some_method(value: MyType) -> int:
    return value.some_method()
```

This way Sematic will ensure that it has a concrete result
before it executes `call_some_method`.
