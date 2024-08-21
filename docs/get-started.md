# Get started

## Supported Platforms

Sematic currently supports Linux and MacOS. If you're using Windows, you can
run Sematic in
[Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/about).

Python versions `3.8` - `3.12` are supported.

## Installation

Install Sematic in your local Python environment with:

```shell
$ pip install sematic
```

The above command will also install all required Python dependencies.

### System Dependencies

Sematic does require an additional system library installed, `libmagic` / `filemagic`,
which is required by [`python-magic`](https://pypi.org/project/python-magic/), in order
to render [`Image`](types.md#the-image-type) type artifacts. If you want to use `Image`s,
you can install the library with:

- MacOs: `brew install libmagic`, or `port install file`
- Debian: `sudo apt-get install libmagic1`
- RPM: `sudo yum install file-devel`
- Windows unofficial support: `pip install python-magic-bin`

## Starting the Web Dashboard

Before running pipelines, you need to start the metadata server and Web Dashboard with:

```shell
$ sematic start
```

This will launch the Dashboard in your browser.

{% hint style="info" %}
This runs the Sematic app on your local machine. To
deploy it within your cloud environment, see [Deploying Sematic](deploy.md).
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

To stop the server, simply do:

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

You can follow execution of the pipeline in the [Web Dashboard](sematic-ui.md),
visualize inputs, outputs, markdown docstrings, etc.

If you want to contribute examples to the Sematic code base, see our
[Contributor Guide](contributor-guide.md).
