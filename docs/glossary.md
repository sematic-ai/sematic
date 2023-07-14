Here is a repository of definitions of terms we use throughout.

## Artifact

Artifacts represent the input and output values of Sematic Functions.

Each individual input argument is tracked as an artifact, and the output value
is tracked as a single artifact.

Artifacts are serialized and summarized for visualization in the UI.

## Cloud execution

Your Sematic pipelines can run on your local machine, which is practical for
iterating, or can run in your cloud (i.e. a Kubernetes cluster in your cloud).
That is Cloud execution.

## Concrete inputs

When Sematic is executing the graph of your pipeline, some of the
values for the input arguments to your Sematic functions can be actual values,
or they can be [Futures](#future), i.e. the output of another Sematic Function.

These actual non-future values are called concrete values.

Within a given Sematic Function, you can be guaranteed that all input arguments
are concrete, because any Future passed as argument will have been determined
prior to executing the current Sematic Function.

## Future

Calling a Sematic Function returns a Future of the output value. It represents a
promise of a future value. See [Future algebra](./future-algebra.md) for more
details.

Sematic uses Futures to perform pseudo-static type checking and to build the
execution graph of your pipeline.

When you call `runner.run(future)` with your pipeline function, Sematic
executes the graph by executing Futures in topological order.

## Parent, child run

See [Run](#run).

In the following example:

```python
@sematic.func
def foo() -> str:
    return "foo"

@sematic.func
def bar() -> str:
    return foo()
```

* `bar`'s run is the *parent* run of `foo`'s run,
* `foo`'s run is a child run of `bar`'s.

Runs can have multiple children runs, but only one parent run.

We sometimes use the following terms interchangeably:

* Parent/child function
* Parent/child future
* Parent/child run

Child runs/functions/futures are also sometimes referred to as "nested".

## Pipeline

In Sematic there is no actual concept of pipeline. We have no abstraction to
describe pipelines.

What we call a "pipeline" is typically the root Sematic Function. It is the
Sematic Function on which you called `runner.run(some_sematic_function())`.

See [Root function](#root-entry-point-function).

## Runners

{% hint style="info" %}
This concept used to be referred to as `Resolvers`. So don't
worry if you're familiar with that terminology! Everything
you know about Resolvers applies to Runners as well, except
that `.resolve(...)` has been renamed to `.run(...)`.
Additionally, futures cann't call `.run(runner)` in the same
way they could call `.resolve(resolver)`. Using the
`runner.run(future)` form is now required.
{% endhint %}

Runners dictate how your pipeline gets "run." Running a pipeline means
going through its DAG (in-memory graph of `Future` objects), and proceeding to
executing each step as its inputs are available.

Different runners offer different execution strategies:

- **`SilentRunner`** – will run a pipeline without persisting anything to
  disk or the database. This is ideal for testing or iterating without poluting
  the database. This also means that pipelines ran with `SilentRunner`
  are not tracked and therefore not visualizable in the web dashboard.
- **`LocalRunner`** – will run a pipeline on the machine where it was
  called (typically you local dev machine). It will persist artifacts and track
  metadata in the database. Runs will be visualizable in the dashboard. No
  parallelization is applied, the graph is topologically sorted. See [Local
  execution](./local-execution.md).
- **`CloudRunner`** – will submit a pipeline to execute on a Kubernetes
  cluster. This can be used to leverage step-dependent cloud resources (e.g.
  GPUs, high-memory VMs, etc.). See [Cloud runner](./cloud-runner.md).

## Pipeline Run

{% hint style="info" %}
This concept used to be referred to as "Resolution". So don't
worry if you're familiar with that terminology! Everything
you know about Resolutions applies to Pipeline Runs as well.
{% endhint %}

A Pipeline Run is one specific execution of a pipeline.

## Root, entry-point function

The root Sematic Function is the one on which you call `.run()`. It is the
parent of all other functions and has no parent itself.

It encapsulates your entire pipeline and all its input values must be
[concrete](#concrete-inputs).

It is the "entry-point" because it is the function you will import and call in
your entry-point script, e.g. `__main__.py`.

In general, we try to call this function `pipeline`, but this is indeed up to you.

## Run

Runs represent the execution of a Sematic Function. Every single Sematic
Function in your graph has a corresponding run when it is executed.

Runs are persisted in the tracking database and visualizable in the UI.

In the following example:

```python
@sematic.func
def add(a: float, b: float) -> float:
    return a + b

@sematic.func
def pipeline(a: float, b: float, c: float) -> float:
    return add(add(a, b), c)
```

Three runs will be persisted:

* One for the `pipeline` function,
* One for `add(a, b)`,
* One for `add(add(a, b), c)`.

## Sematic Function

See [Sematic Functions](./functions.md).

## Standalone, Inline Function

When executed with `CloudRunner`, by default, all Sematic Functions run
"non-standalone". That means they execute in the same Kubernetes container as the
`CloudRunner` which orchestrates the pipeline.

Standalone Functions run in their own Kubernetes container, job, and pod. They
can therefore request custom resource requirements:

```python
@sematic.func(standalone=True, resource_requirements=GPU_RESOURCE_REQS)
def foo():
    ...
```

See [Customize resource
requirements](./cloud-runner.md#customize-resource-requirements) for more
info.

## Upstream, downstream Function

In the following example:

```python
@sematic.func
def foo():
    ...

@sematic.func
def bar(a):
    ...

@sematic.func
def pipeline():
    a = foo()
    b = bar(a)
    return b
```

* `foo` is the **upstream** function/future/run of `bar`,
* `bar` is the **downstream** function/future/run of `foo`.

## Tag

Tags are short strings you can associate with runs that can help you
organize and search for runs. To use them, set the `tags` property on
a future before calling `runner.run(future)` with it.

```python
pipeline().set(tags=["my-tag", "size:large"])
```

In this example, a run of the pipeline will have two tags associated
with it: `my-tag` and `size:large`. Both will be displayed with the run
in the dashboard and be usable in the run search page.