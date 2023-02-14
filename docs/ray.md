# Ray[^1]

{% hint style="warning" %}
This feature is in "Beta."
{% endhint %}

{% hint style="info" %}
This feature is only available in Sematic
Enterprise Edition.
{% endhint %}

## What is Ray?

[Ray](https://www.ray.io/) is a framework for scaling python
workloads, with an emphasis on AI/ML workloads. It has integrations
to allow data processing, distributed training, hyperparameter
tuning and more. It can be used with Sematic to "scale out" your
individual steps (ex: use
[Ray's pytorch integrations](https://docs.ray.io/en/latest/train/api.html#pytorch)
to do distributed training within a single Sematic func for training).
Sematic can then be used to chain together your high-level ML pipeline
(do data processing, then feed the result into training, then feed
the result into evaluation, etc.).

## Using Ray in a Sematic func

{% hint style="info" %}
**Important**: Before you can use this feature, you need to
[install and configure](#installation-and-configuration)
the integration.
{% endhint %}

Using Ray within Sematic is as simple as using `with RayCluster(...)`
inside a `@sematic.func`:

```python
import ray
from ray.train.torch import TorchTrainer
from ray.air.config import ScalingConfig
from ray.train.torch import TorchCheckpoint
from sematic.ee.ray import RayCluster, RayNodeConfig, SimpleRayCluster

@sematic.func
def train(
    dataset: MyDatasetReference,
    training_config: MyTrainingConfig,
) -> MyModel:
    n_workers = training_config.n_workers
    with RayCluster(
        config=SimpleRayCluster(
            n_nodes=n_workers,
            node_config=RayNodeConfig(cpu=16, memory_gb=32, gpu_count=1),
        )
    ):
        trainer = TorchTrainer(
            train_loop_per_worker=my_train_func,
            train_loop_config=training_config.train_loop_config(dataset),
            scaling_config=ScalingConfig(num_workers=n_workers, use_gpu=True),
        )

        # Start distributed training using our ephemeral Ray cluster
        result = trainer.fit()
        model = TorchCheckpoint.from_checkpoint(result.checkpoint).get_model(MyModel())
        return model
```

When you use this code, it will:

- Start up an ephemeral Ray cluster. If using the `LocalResolver`, the cluster will
be backed by local processes. If using the `CloudResolver`, the cluster will be
backed by Ray workers that are spun up on your Kubernetes worker.
- Ensure your dependencies are usable for training. Anything you can `import` and
use in your Sematic functions can automatically be imported and used for the code
running on the Ray cluster. The same docker image managed by Sematic will be
used by the Ray workers, so even native dependencies (ex: cuda) are available.
- Only enter the `with RayCluster` block once your cluster is ready to be used.
- Forward logs from Ray workers back to Sematic for display in the Sematic dashboard.
- Execute your training code on the Ray cluster.
- Tear down the cluster when training terminates (successfully or with a failure).

### Detailed API

#### RayCluster

A representation of the cluster that will be created.

- **config** (*[`RayClusterConfig`](#rayclusterconfig)*): A configuration for
the compute resources that will be started. If using LocalResolver or
SilentResolver, this will be ignored and a local cluster will be started instead.
- **forward_logs** (*bool*): Whether or not to have logs from Ray workers returned
back to the stdout of the Sematic func this resource is used in. Sets `log_to_driver`
in [`ray.init`](https://docs.ray.io/en/latest/ray-core/package-ref.html?highlight=init#ray.init)
- **activation_timeout_seconds** (*float*): The number of seconds the cluster has
to initialize itself before a timeout error occurs.

#### RayClusterConfig

Represents the compute resources the cluster will use. Allows using autoscaling
of the Ray cluster, configuring multiple scaling groups with different
characteristics, and using workers that differ from the head. If you wish
to create a `RayClusterConfig` with a fixed number of identical workers,
see [`SimpleRayCluster`](#simpleraycluster)

- **head_node** (*[`RayNodeConfig`](#raynodeconfig)*): The configuration
for the head node.
- **scaling_groups** (*[`List[ScalingGroup]`](#scalinggroup)*): A list of
scaling groups. Each scaling group may have different properties for the
nodes in the group.

#### SimpleRayCluster

Utility function for creating [`RayClusterConfig`](#rayclusterconfig) for
clusters with a fixed number of uniform workers.

- **n_nodes** (*int*): The number of nodes in the cluster, including the
head node
- **node_config** (*[`RayNodeConfig`](#raynodeconfig)*): The configuration
for each node in the cluster

#### RayNodeConfig

The compute characteristics of a single Ray head/worker.

- **cpu** (*float*): Number of CPUs for each node (supports fractional CPUs).
- **memory_gb** (*float*): Gigabytes of memory for each node
(supports fractional values).
- **gpu_count** (*int*): The number of GPUs to attach. Not all deployments
support GPUs, or more than one GPU per node.

#### ScalingGroup

A group of workers that all have the same compute characteristics.

- **worker_nodes** (*[`RayNodeConfig`](#raynodeconfig)*): A description
of the compute resources available for each node in the scaling group.
- **min_workers** (*int*): The minimum number of workers the scaling
group can scale to. Must be non-negative.
- **max_workers** (*int*): The maximum number of workers the scaling
group can scale to. Must be equal to or greater than min_workers.
For a fixed-size scaling group, set this equal to min_workers.

## Installation and configuration

Before using this feature, make sure you are set up with a Sematic EE
license. Once that's taken care of, you will need to make the following
changes:

### Pip package

Instead of depending on `sematic`, you will need to depend on `sematic[ray]`
or `sematic[all]`.

### Helm chart

Ensure that you are using an [EE server](./upgrades.md#foss-to-enterprise-edition1).
Then you will need to install Kuberay into your Kubernetes environment.

#### Installing Kuberay

This can be done via helm, with instructions
[here](https://ray-project.github.io/kuberay/deploy/helm/). Please install the latest
stable version, and not the nightly one! You probably want to use a
`singleNamespaceInstall`  (see
[here](https://github.com/ray-project/kuberay/blob/2600854c61673f2b7da9fe2b54c8220468c1a013/helm-chart/kuberay-operator/values.yaml#L62)) and install it in the same namespace as Sematic. You will probably want to apply
a configuration for a simple ray cluster (such as
[this](https://github.com/ray-project/kuberay/blob/master/ray-operator/config/samples/ray-cluster.complete.yaml))
to verify the deployment. You can delete that cluster once you have verified that the
appropriate pods are created and are marked as ready.

#### Configuring values.yaml

You will want to set `rbac.manage_ray` to `true` to ensure that the
Sematic server has permissions to manage Ray clusters. Then configure
all the values called `ray.*`, as described in Sematic's
[Helm documentation](https://github.com/sematic-ai/helm-charts/blob/gh-pages/README.md).

As an example, your completed `ray.*` configs might look something like the following.
However, do note that different configurations and deployments of Kubernetes will
require/support different node selectors, tolerations, etc..

```yaml
ray:
  enabled: true
  supports_gpus: true
  gpu_node_selector: {"node.kubernetes.io/instance-type": "g4dn.xlarge"}
  non_gpu_node_selector: {}
  gpu_tolerations:
    - key: "nvidia.com/gpu"
      value: "true"
      operator: Equal
      effect: NoSchedule
  non_gpu_tolerations: []
  gpu_resource_request_key: null
```

[^1]: This feature of Sematic is only available with the "Enterprise Edition."
Before using, please reach out to Sematic to obtain a license for "Sematic EE."
