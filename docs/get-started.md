# Get started

## Installation

First, let's install Sematic

```shell
$ pip install sematic
```

## Starting the app

Now you should be able to launch the Sematic App on your local machine with

```shell
$ sematic start
```

This will open the app in your browser.

{% hint style="info" %}
This runs the Sematic app on your local machine. To
deploy it within your cloud see [Deploying Sematic](deployment.md).
{% endhint %}

To stop the app, simply do

```shell
$ sematic stop
```

## Running an example pipeline

Sematic comes with a number of pre-packaged examples.

To run an example pipeline (e.g. MNIST in PyTorch), do:

```shell
$ sematic run examples/mnist/pytorch
```

See all available examples at
[sematic/examples](https://github.com/sematic-ai/sematic/tree/main/sematic/examples).


{% hint style="info" %}
In order to make sure Sematic remains as light as
possible, expensive dependencies such as PyTorch or Pandas are not included out
of the box. If they are missing on your machine, Sematic will let you know how
to install them.
{% endhint %}

You can follow execution of the pipeline in the [Sematic UI](sematic-ui.md), visualize inputs, outputs,
markdown docstrings, etc.

If you want to contribute examples to the Sematic code base, see our
[Contributor Guide](contributor-guide.md).
