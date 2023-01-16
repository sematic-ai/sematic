# Writing your first pipeline

## Create a new project

To write your first pipeline, start by creating a project:

```shell
$ sematic new hello_world
```

This will simply create a Python package with some boilerplate code to get you started.

```shell
$ ls hello_world
    __init__.py
    __main__.py
    pipeline.py
    requirements.txt
    README
```

The following files are present in the `hello_world/` directory:

* `__main__.py` – This is the typical entry point of any Python package. As you
  can see it is a very standard Python script that you can parametrize
  arbitrarily with command-line arguments using
  [`argparse`](https://docs.python.org/3/library/argparse.html).
* `pipeline.py` – This is where your pipeline and its nested steps are defined. As your
  code gets more complex, it is recommended to break it down into further sub-modules (e.g. `train.py`, `eval.py`, etc.). Of course you can define multiple pipelines and pilot their executions from the `__main__.py` script.
* `requirements.txt` – This is where you can keep the external dependencies specific to your project.

{% hint style="info" %}
You can create a new project directly from an existing example with 

```shell
$ sematic new hello_world --from examples/mnist/pytorch
```

This will simply copy the entire pipeline's code into your new project.

{% endhint %}


## Hello-world pipeline

In `hello_world/pipeline.py`, write the following code:

```python
@sematic.func
def hello_world() -> str:
    return "Hello world"

@sematic.func
def my_name_is(name: str) -> str:
    return "my name is {}".format(name)

@sematic.func
def nice_to_meet_you(hello: str, name_is: str) -> str:
    return "{}, {}. Nice to meet you.".format(hello, name_is)

@sematic.func
def pipeline(name: str) -> str:
    """
    My very first hello-world Sematic pipeline.
    """
    hellow = hello_world()
    name_is = my_name_is(name)
    return nice_to_meet_you(hellow, name_is)
```

In `hello_world/__main__.py`, write the following code:

```python
import argparse

from hello_world.pipeline import pipeline

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Hello World")
    parser.add_argument("--name", type=str, required=True)

    args = parser.parse_args()

    pipeline(args.name).resolve()
```

Now you can run it with

```shell
$ python3 -m hello_world --name "Knight who says Nee"
```

You can now follow execution of the pipeline in the dashboard. For a tour,
see [Web dashboard](sematic-ui.md).

{% hint style="info" %}

Obviously this toy pipeline is not very useful. Here are a number of things you
can do in Sematic functions:

* Anything that can be expressed in Python
* Load, process, and  filter dataframes
* Launch a data processing job (e.g. Spark, Google Dataflow)
* Train a model, launch a training job on a dedicated service
* Query a database or data warehouse
* Query an API

Really anything you can do in Python 🙂. See [Capabilities](./capabilities.md)
for a discussion of what Sematic can support.

For a more realistic pipeline, see [The MNIST pipeline](./real-example.md).

{% endhint %}

## What happens when I decorate a function with `@sematic.func`?

The `@sematic.func` decorator converts any plain Python function into a
so-called ["Sematic Function"](functions.md). Sematic functions are tracked by
Sematic as pipeline steps. This means that their inputs and outputs are
type-checked and tracked as [Artifacts](glossary.md#artifact), and that you will
be able to inspect and visualize the function's execution in the UI.

In the case of [cloud execution](glossary.md#cloud-execution), each function can
run as its own isolated container with its own set of resources.

{% hint style="info" %}

Note that calling a Sematic Function returns a **Future** instead of the actual
value returned by the decorated Python function. Read more about Futures in
[Future algebra](future-algebra.md).

Futures are the way Sematic constructs the execution graph of your pipeline.
Futures support a subset of native Python's operation, although we are adding
new functionalities every week. See [Future Algebra](future-algebra.md) for more
details.

In order to trigger the actual execution of a graph, you need to call
`.resolve()` on the entry point of your graph, that is typically the function
called `pipeline`. See the [Glossary](glossary.md#pipeline) for more details.

{% endhint %}

## What happens when I call `.resolve()` on the `pipeline` function?

Calling `resolve` will trigger the actual "resolution" of your pipeline's
execution graph. Sematic will do the following things:

* Perform some "pseudo-static" type checking to ensure connected pipeline steps
  do not have incompatible types (e.g. passing a `bool` to a function requiring
  an `int`). See [Type support](type-support.md) for more details.
* Start resolving the nested graph layer by layer. See [Graph
  resolution](graph-resolution.md) for more details.
* For each layer, Sematic will resolve Futures (your functions) in topological
  order (parallelizing execution when possible depending on the chosen
  resolution strategy).
* For each individual function
    * the concrete input values are type-checked against the type annotations
  you have specified in your function's signature
    * input artifacts (individual function arguments) are serialized and persisted for tracking and visualization
    * the function gets executed
    * the output value is type-checked against the declared output type
    * the output artifact is serialized and persisted for tracking and visualization

{% hint style="info" %}

`.resolve()` should be called **only  once** per pipeline. If you want to nest
pipeline steps, simply call the function and return the resulting Future.

{% endhint %}
  
## Dive into more details

If you want to learn more, explore the following resources:

* A growing list of [Example pipelines](https://github.com/sematic-ai/sematic/tree/main/sematic/examples)
* More details about [Sematic Functions](functions.md)
* All about types: [Type support](type-support.md)
* Operations supported on Futures: [Future algebra](future-algebra.md)
* Sematic's [Graph resolution](graph-resolution.md) mechanism
* [Glossary](glossary.md) for all the definitions