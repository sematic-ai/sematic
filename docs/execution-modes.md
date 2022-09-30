Sematic aims to make your development workflow faster and more efficient.

It is quite typical to start iterating on a pipeline locally, e.g. on 1% of the
data, and then run it at scale in the cloud.

Sematic enables this seamlessly by aiming to guarantee a local-to-cloud parity.
This means that if your pipeline runs succesfully locally, it should run
succesfully at scale on the cloud.

Of course there are many reasons why a cloud pipeline could fail that are not
forseeable locally. For example: network failures, Out-of-memory issues,
differences in underlying hardware (CPU, GPU, etc.), invalid data not present in
your local 1%, rare corner cases, etc.

But when it comes to building your code, correctness of your type hints and
syntax, and dependency packaging, Sematic can do a great deal to save you from a lot
of wasted time.

In Sematic, how your pipelines execute is dictated by your choice of **Resolver**.

Sematic provides the following resolution strategies:

## Silent resolution

`SilentResolver` runs your code locally (i.e. on your machine) and does not
write anything to the database. Your pipeline will not show up in the UI.

This is useful for quick debugging in a Python console, or writing tests.

To use this mode, simply do:

```
>>> from sematic import SilentResolver
>>> pipeline(...).resolve(SilentResolver())
```

## Local resolution

`LocalResolver` is the default resolver. Your pipeline still runs on your local machine, but
tracks execution in Sematic's database. Your pipeline's runs and artifacts are
visualizable in the UI.

To use this mode, simply do:

```
>>> pipeline(...).resolve()
```

{% hint style="info" %}

Out of the box, Sematic writes to a local database sitting on your local machine,
and the UI also runs in a local server.

To be able to share results with your team, it is best to deploy Sematic in your
cloud infrastructure. See [Deploy Sematic](./deploy.md).


{% endhint %}

## Cloud resolution

With `CloudResolver` you can resolve your pipeline on a remote Kubernetes cluster.

Each Sematic Function in your pipeline can have its own Kubernetes job with
dedicated resources (e.g. GPUs).

{% hint style="info" %}

**Prerequisite:** To learn how to deploy Sematic in your cloud, read
[Deploy Sematic](./deploy.md) and [Container images](./container-images.md).

{% endhint %}

To use `CloudResolver`, simply do

```python
from sematic import CloudResolver

pipeline(...).resolve(CloudResolver())
```


`CloudResolver` may launch two types of Kubernetes jobs on your behalf:

* **Driver job** – this is the job that orchestrate your pipeline. It runs
  functions and potentially launches dedicated jobs for them (see `inline` below), waits for
  completion, serializes artifacts, etc. The driver job holds the execution
  graph of your pipeline in memory and resolves it, parallelizing functions when
  possible.

  There can be zero or one (see `detach` below) driver job per pipeline execution.

* **Worker jobs** – this is the job that runs a single Sematic Function (if
  `inline=False`, see below). It is solely responsible for fetching input
  arguments, type-checking them, executing the Sematic Function, type-checking
  its output, and persisting it.
  
  For each pipeline execution, there can be
  between zero worker jobs (all functions are `inline=True`) and one worker job
  per Sematic Function (all functions are `inline=False`).

As mentioned above there are two parameters you can set to decide how and where
your jobs are running.


|Parameter| Usage| `True` | `False` | default |
|-|-|-|-|-|
|`detach`| `CloudResolver(detach=<value>)`| The **driver job** will run in a remote Kubernetes job. This is the so-called "fire-and-forget" mode. Your console prompt will return as soon as the driver job is submitted. | The **driver job** will run on your local machine. The console prompt will return only after the entire pipeline has resolved. | `True` |
|`inline`| `@sematic.func(inline=<value>)`| The Sematic Function will run within the driver job, whether on your local machine or in a remote job (according to `detach`). | The corresponding Sematic Function will run in its own Kubernetes job, whose resource can be customized (see Resource Requirements). Note that nested functions do not inherit their parent's `inline` value. | `True`

To summarize, by default (`detach=True` and `inline=True`) your entire pipeline will run in a single Kubernetes job (the driver job). Then you can choose which functions should have their own Kubernetes job (and resources) by setting `inline=False` on the corresponding function.

Note that choosing `detach=False` and setting `inline=True` on all your Sematic Functions is essentially equivalent to using `LocalResolver`.

### Resource requirements

You can select what hardware resources are available to each job by passing a
`resource_requirement` argument to `@sematic.func`.

For example:

```python
from sematic import ResourceRequirements, KubernetesRequirements

GPU_RESOURCE_REQS = ResourceRequirements(
    kubernetes=KubernetesRequirements(
        # Note: the kind of node selector options that are valid will depend on
        # your particular deployment of Kubernetes. Talk to the person who manages
        # your Kubernetes cluster if you think you might need this. It is primarily
        # useful in Sematic to gain access to nodes with GPUs.
        node_selector={"node.kubernetes.io/instance-type": "g4dn.xlarge"},

        # The resource requirements of the job. Information on the format of valid
        # values can be found here: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
        # the dictionary provided here will be used for both "limits" and "requests"
        requests={"cpu": "1", "memory": "1Gi"},
    )
)

@sematic.func(resource_requirements=GPU_RESOURCE_REQS)
def train_model(...):
    ...
```

Note that the corresponding instances need to have been provisioned in your
Sematic cluster ahead of time.

### Understanding "Inline"

Before understanding inline functions, it is first helpful to refresh yourself
on the description of the "driver" job above. Note that this job is distinct
from the container where the root run executes - it's best to think of the
driver as an "extra" container for the overall pipeline.

Given this understanding of the driver job, the behavior of inline executions
can be summarized as follows. Every Sematic func executes in one of two places:

(1) The driver container
(2) Its own, dedicated container

The *only* determining factor in which of these two is used for a given function
is whether or not it has `inline=True`. For functions where `inline=True`, they
will execute in the driver container. This is best used for very lightweight
functions that execute quickly and don't make any calls to external services. For
functions where `inline=False`, they execute in their own containers.

A common source of confusion with inline functions is to think there's a
relationship between nested functions and inline. Consider the following code:

```python
@sematic.func(inline=False)
def calculate_average(a: float, b: float, c: float) -> float:
  total = add(a, b, c)
  average = divide(total, 3)

@sematic.func(inline=False)
def add(a: float, b: float, c: float) -> float:
  return a + b + c

@sematic.func(inline=True)
def divide(a: float, b: int) -> float:
  return a / b
```

Let's assume `calculate_average` and `add` are actually doing something
"heavy" that requires a dedicated container, rather than just performing
simple arithmetic operations.

People sometimes assume that since `divide`
is nested inside `calculate_average`, and `divide` is inline, `divide`
must execute in the same container as `calculate_average`. This is NOT
correct. This misunderstanding stems from a misunderstanding of how Sematic
works with Futures. Recall that Sematic functions return futures when you
call them. That means that `total` in `calculate_average`
*actually holds a Future instead of a `float`*. So when `divide(total, 3)`
is called above, the content of `total` is not even known. Therefore how
could it be executed?

Instead, what happens is this:

1. `add` is called and immediately returns a Future without doing any work
2. `divide` is called, given the Future from `add` and the constant `3`. It
also returns immediately without doing any work.
3. `calculate_average` returns the `Future` output by `divide`
4. The driver job analyzes the `Future` coming from `calculate_average` and
sees that to get the value for it, it must first execute `add` and then
execute `divide`.
5. Since `add` is non-inline, the driver starts a container within which to
execute `add`. `add` returns an actual `float` which is the sum of `a`, `b`, and
`c`.
6. The driver sees that it now has everything required to execute `divide`, so
it does so. Since `divide` is inline, the driver doesn't need to start a new
container for it, and instead it executes `divide` in its own process.

#### When to use inline?

After walking through the above example, you may be wondering if there's a simple
way to know when something should be marked as inline vs not. Even if you don't
follow the above trace of the execution, you can still use `inline` correctly if
you follow this guidance:

- Any Sematic function doing something "trivial" that executes in a few seconds or
less and requires negligible CPU or memory should be inline.
- Any Sematic function which primarily calls other Sematic functions and doesn't
do any work "of its own" aside from these calls should be inline
- Any other Sematic functions should NOT be inline. In practice this usually means
"leaf node" Sematic functions that don't call other Sematic functions and which
do some "real work."

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

### Dependency packaging

When Sematic submits Kubernetes jobs, it needs to package all your dependencies
(e.g. your pipeline code, local Python modules, third-party pip packages, static
libraries, etc) and ship them to the remote cluster. For more on how Sematic
handles dependency packaging, see
[Sematic and Container Images](./container-images.md)
