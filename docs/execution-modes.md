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

At this time this only allows you to pass a node selector to choose a node in
your Kubernetes cluster. In the future, we will also surface CPU, memory, and
ephemeral storage requirements.

Note that the corresponding instances need to have been provisioned in your
Sematic cluster ahead of time.

### Dependency packaging

When Sematic submits Kubernetes jobs, it needs to package all your dependencies
(e.g. your pipeline code, local Python modules, third-party pip packages, static
libraries, etc) and ship them to the remote cluster. For more on how Sematic
handles dependency packaging, see
[Sematic and Container Images](./container-images.md)
