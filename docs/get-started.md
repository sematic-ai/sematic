# Get started

Welcome to Sematic, let's get you set up.

## Installation

First, let's install Sematic

```shell
$ pip install sematic
```

## Starting the app

Now you should be able to launch the Sematic App by issuing

```shell
$ sematic start
```

That will open the app in your browser.

{% hint style="info" %} At this time, Sematic runs on your local machine. Soon we will enable you to host it in your cloud. {% endhint %}

If you want to stop the app, simpy issue

```shell
$ sematic stop
```

## Running an example pipeline

To run an example pipeline, for example MNIST in PyTorch, issue:

```shell
$ sematic run examples/mnist/pytorch
```

{% hint style="info" %} Sematic does not include expensive dependencies such as PyTorch or Pandas out of the box. If they are missing on your machine, Sematic will let you know how to install them. {% endhint %}

The UI should open the Pipeline Page for the MNIST pipeline and you can follow execution and inspect inputs and outputs.

## Writing your own pipeline

To write your own pipeline, create a Python file and paste the following code.

```python
@sematic.func
def add(a: float, b: float) -> float:
    return a + b

@sematic.func
def pipeline(a: float, b: float) -> float:
    return add(add(a, b), add(a, b))

if __name__ == "__main__":
    pipeline(1, 2).resolve()
```

And run

```shell
$ python3 pipeline.py
```

That's it!
