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

**Prerequisite:** To learn how to deploy Sematic in your cloud, read [Deploy Sematic](./deploy.md).

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
|`inline`| `@sematic.func(inline=<value>)`| The corresponding Sematic Function will run in its own Kubernetes job, whose resource can be customized (see Resource Requirements). Note that nested functions do not inherit their parent's `inline` value. | The Sematic Function will run within the driver job, whether on your local machine or in a remote job (according to `detach`). | `True`

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
        node_selector={"node.kubernetes.io/instance-type": "g4dn.xlarge"}
    )
)

@sematic.func(resource_requirements=GPU_RESOURCE_REQS)
def train_model(...):
    ...
```

At this time this only allows you to pass a node selector to choose a node in
your Kubernetes cluster. In the future, we will also surface CPU, memory, and
ephemeral storage requirements.

### Dependency packaging

When Sematic submits Kubernetes jobs, it needs to package all your dependencies
(e.g. your pipeline code, local Python modules, third-party pip packages, static
libraries, etc) and ship them to the remote cluster.

At this time, Sematic leverages [**Bazel**](https://bazel.build) to package and
ship dependencies. This is convenient with users working in a monorepo that is
already using Bazel. For others, Sematic will soon provide a native dependency
packaging solution.

#### Bazel macro

Sematic offers a `sematic_pipeline` Bazel rule to pilot your pipelines.

To use it, make sure that the `rules_python` `io_bazel_rules_docker` HTTP
archives are set up and add the following directive are in your `WORKSPACE`
file.

```starlark
# Bazel WORKSPACE file

# rules_python archive and toolchain

# io_bazel_rules_docker archive

load(
    "@io_bazel_rules_docker//repositories:repositories.bzl",
    "repositories",
)

repositories()

## SEMATIC RULES

load("@bazel_tools//tools/build_defs/repo:git.bzl", "git_repository")

git_repository(
    name = "rules_sematic",
    branch = "main",
    remote = "git@github.com:sematic-ai/sematic.git",
    strip_prefix = "bazel",
)

load("@rules_sematic//:pipeline.bzl", "base_images")

base_images()

```

Then in your package's `BUILD` file do

```
# BUILD file at path/to/pipeline

load("@rules_sematic//:pipeline.bzl", "sematic_pipeline")
load(
    "@rules_python//python:defs.bzl",
    "py_library",
)
load("@<your-dependency-repo>//:requirements.bzl", "requirement")

py_library(
    name = "main_lib",
    srcs = [
        "main.py",
        "pipeline.py",
        ...
    ],
    deps = [
        requirement("sematic"),
        ...
    ],
)

sematic_pipeline(
    name = "main",  # the entry point of your pipeline is main.py
    registry = "<container-registry-uri>",
    repository = "<container-repository>",
    deps = [
        ":main_lib",
    ],
    # Optional base image to use
    base = "<base-image>",
    # Optional environment variables to set in the image
    env = {"VAR": "VALUE"} 
)
```

See a complete example at
[github.com/sematic-ai/example-bazel](https://github.com/sematic-ai/example-bazel).

You can then run the target with

```
$ bazel run //my_repo/path/to/pipeline:main -- --arg1 --arg2
```

where `--arg1` and `--arg2` are your entry point's (`main.py`) command line
arguments.

This will perform the following actions:

* Package all declared dependencies into a Docker image (if they have changed)

* Registers the image with your container registry

* Execute your entry point

Packaging dependencies can be somewhat slow, so if you want to simply test your
pipeline locally, you can use the `<target-name>_local` target:

```
$ bazel run //my_repo/path/to/pipeline:main_local -- --arg1 --arg2
```

This will skip the dependency packaging and image registration parts. Note that
in this case, if your code attempts to submit remote jobs, it will fail as no image was produced.