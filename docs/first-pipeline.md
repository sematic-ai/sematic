# Writing your first pipeline

## Create a new project

To write your own pipeline, start by creating a project:

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
* `pipeline.py` – This is where your pipeline and its steps are defined. As your
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

Now you can it with

```shell
$ python3 -m hello_world --name "Knight who says Nee"
```

You can now follow execution of the pipeline in the UI. For a tour of the UI
sees [Sematic UI](sematic-ui.md).