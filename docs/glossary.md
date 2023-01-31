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

When Sematic is resolving the execution graph of your pipeline, some of the
values for the input arguments to your Sematic functions can be actual values,
or they can be [Futures](#future), i.e. the output of another Sematic Function.

These actual non-future values are called concrete values.

Within a given Sematic Function, you can be guaranteed that all input arguments
are concrete, because any Future passed as argument will have been resolved
prior to executing the current Sematic Function.

## Future

Calling a Sematic Function returns a Future of the output value. It represents a
promise of a future value. See [Future algebra](./future-algebra.md) for more
details.

Sematic uses Futures to perform pseudo-static type checking and to build the
execution graph of your pipeline.

When you call `.resolve()` on your pipeline function, Sematic "resolves" the
graph by executing Futures in topological order.

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
Sematic Function on which you called `.resolve()`.

See [Root function](#root-entry-point-function).

## Resolvers

Resolvers dictate how your pipeline gets "resolved". Resolving a pipeline means
going through its DAG (in-memory graph of `Future` objects), and proceeding to
executing each step as its inputs are available.

Different resolvers offer different resolution strategies:

- **`SilentResolver`** – will resolve a pipeline without persisting anything to
  disk or the database. This is ideal for testing or iterating without poluting
  the database. This also means that pipelines resolved with `SilentResolver`
  are not tracked and therefore not visualizable in the web dashboard.
- **`LocalResolver`** – will resolve a pipeline on the machine where it was
  called (typically you local dev machine). It will persist artifacts and track
  metadata in the database. Runs will be visualizable in the dashboard. No
  parallelization is applied, the graph is topologically sorted. See [Local
  execution](./local-execution.md).
- **`CloudResolver`** – will submit a pipeline to execute on a Kubernetes
  cluster. This can be used to leverage step-dependent cloud resources (e.g.
  GPUs, high-memory VMs, etc.). See [Cloud resolver](./cloud-resolver.md).

## Resolution

A Resolution is one specific execution of a pipeline.

## Root, entry-point function

The root Sematic Function is the one on which you call `.resolve()`. It is the
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

## Upstream, downstream function

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