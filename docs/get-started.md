# Get started

## Supported Platforms

Sematic currently supports Linux and Mac. If you're using Windows, you can
run Sematic in
[Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/about)

We support Python versions 3.8 & 3.9

## Installation

Make sure you are using a supported platform, then install Sematic:

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
If you want to run the local version of the app for yourself, but
access it from a different machine (ex: if you are running the
app from within a docker container or on a cloud development
machine), you can launch with
```shell
$ SEMATIC_SERVER_ADDRESS=0.0.0.0 sematic start
```
but this mechanism of running the server is still only
intended for single-user usage.
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
