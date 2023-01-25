In Sematic, resolvers implement different so-called "resolution" strategies. For
example, as described in [Local execution](./local-execution.md),
`LocalResolver` will resolve your pipeline graph and execute all steps on your local machine.

`CloudResolver` will resolve your pipeline graph in a Kubernetes cluster.

{% hint style="info" %}

### Prerequisite

In order to execute Sematic pipelines on a Kubernetes cluster, the API server
and web dashboard need to be deployed in said cluster. See [Deploy
Sematic](./deploy.md).

{% endhint %}

## `CloudResolver` usage

In order to use `CloudResolver`, simply pass an instance to your top-level
Sematic Function's `resolve` method:

```python
pipeline(...).resolve(CloudResolver())
```

This makes the assumption that a container image was built and registered with a
container registry. At this time, Sematic only supports Bazel as a way to build
and register Docker images at runtime. See [Container
images](./container-images.md).

## Execution on Kubernetes

Sematic will run two types of pods for each pipeline:

* **Driver pod** – this is where the graph of your pipeline gets processed,
  and where the `Resolver` and `inline=True` pipeline steps run. This pod
  has the word "driver" in its name.
* **Worker pods** – this is where individual pipeline steps will be run if they
  are marked as `inline=False`. These pods have the work "worker" in their name.

By default, the resolution of the graph and all pipeline steps will run in a
single pod, the resolver pod. This is fine for minor pipeline steps that take up
little time and resources. Some pipeline steps may require specific resources
(e.g. GPUs) and need to run in their own isolated containers. This can be
achieved as follows:

```python
@sematic.func(inline=False)
def train_model(...):
    ...
```

`inline=False` functions will be executed asynchronously as separate Kubernetes pods.

## Customize resource requirements

Sematic lets you customize what resources to allocate to particular pipeline
steps (Sematic Functions).

Pass a `ResourceRequirements` object to the Sematic decorator as follows:

```python
@sematic.func(
    inline=False,
    resource_requirements=ResourceRequirements(
        kubernetes=KubernetesResourceRequirements(
            node_selector={"node.kubernetes.io/instance-type": "g4dn.xlarge"},
            requests={"cpu": "2", "memory": "4Gi"},
        )
    )
)
def train_model(...):
    ...
```

If there is a corresponding node available in your Kubernetes cluster, this
function will be executed on that node.

Note that `inline=False` is necessary for these resource requirements to be
honored, otherwise, they will be ignored.

{% hint style="info" %}

### Logging

By default Sematic will ingest logs for remote runs and display them
in the dashboard. However, if you wish to have the logs from remote
executions go directly to the pod's stdout/stderr without Sematic
attempting to ingest them, you can configure the user setting
`SEMATIC_LOG_INGESTION_MODE=off`. Like all other user settings, this
can be overridden by environment variables.

{% endhint %}