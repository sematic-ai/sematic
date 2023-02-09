# Upgrades

This page contains some guidance on upgrading an existing deployment of Sematic
in various circumstances.

## General guidance

Sematic has 3 components, depending on your usage:

- *pip package*: If you are using Sematic only locally, this is
the only component you need.
- *Server*: If you are using Sematic in the cloud, you need this
and the pip package.
- *bazel integration*: If you are using `bazel` with Sematic, you
need this component as well.

When you are upgrading Sematic, you generally want to upgrade all of
the components you are using at the same time. It is impossible to
upgrade all of them literally atomically, so we reccommend upgrading in
the order:

- Server
- bazel integration
- pip package

Newer servers are often compatible with older pip packages, but pip
packages cannot be newer than the server they are interacting with.

To see which pip packages a given server version supports, check the
[release notes](https://github.com/sematic-ai/sematic/releases).

Pip packages and the bazel integration should always be kept in sync.

### Upgrading the pip package

If you have installed via command line, you can do the following
to upgrade to the latest:

```bash
pip install sematic --upgrade
```

or to install a specific version:

```bash
pip install sematic==X.Y.Z
```

If you use a `requirements.txt` file or similar, you can increase the version
there and then install from the `requirements.txt` file.

### Upgrading the bazel integration

Your bazel `WORKSPACE` should contain something like the following:

```python
git_repository(
    name = "rules_sematic",
    remote = "https://github.com/sematic-ai/sematic.git",
    strip_prefix = "bazel",
    tag = "vX.Y.Z",
)
```

To upgrade, change the `tag` to the version you wish to install (should match
the pip package).

### Upgrading the Server

The server should be installed via `helm`. Make any adjustments to your `values.yaml`
required by the latest version (See the section
["From vX1.X2.X3 to vY1.Y2.Y3"](#from-vx1x2x3-to-vy1y2y3) below). Then:

```bash
helm upgrade sematic-server -f /path/to.values.yaml
```

## Upgrading the server past supported client versions

You will always want to upgrade the server before upgrading the clients. If the
server is being upgraded to a version that still supports the version being
used by your clients, you can often upgrade the server without any downtime for
users. This is one benefit of keeping up-to-date with regular upgrades! If you
want to know what client versions a given server supports, you can look at
the [release notes](https://github.com/sematic-ai/sematic/releases).

Often, you will need to upgrade the server beyond support for the clients
currently in use. When this happens, a recommended upgrade workflow is:

1. Draft a PR in your repo that upgrades the clients
2. Notify users that there will be an upcoming maintenance window for upgrades
   during which they may not be able to use Sematic.
3. When the maintenance window arrives, upgrade the server.
4. Test the clients using the branch for your upgrade PR. Assuming all goes
   well, merge the PR. If not, roll back the server.
5. Notify users that the maintenance window is now complete and that they will
   need to merge the main branch into their feature branches to begin using the
   latest version.

## From vX1.X2.X3 to vY1.Y2.Y3

This section contains instructions for migrating from one
version of Sematic to another. It does not cover every version
delta, but only (a) from one version to a subsequent one (b)
upgrades where there are non-trivial details to pay attention to
when performing the upgrade.

### v0.23.X to v0.24.Y

#### Server/Helm upgrade notes

You will need to make the following changes to the `values.yaml`
for your Helm deployment:

- If you are NOT using Sematic "Enterprise Edition",
change `image.repository` from `sematicai/sematic-server`
to `sematic/sematic-server`.
- You may have hard-coded a Sematic version in `image.tag`
to work around the bug referenced in
[this PR](https://github.com/sematic-ai/sematic/pull/534). If so,
you may now remove the hard code of `image.tag` to again rely
on the default behavior of using the version from the
[`Chart.yaml`](https://github.com/sematic-ai/sematic/blob/main/helm/sematic-server/Chart.yaml)
for the chart you install.
- If you are specifying `ingress.dashboard_url`, change the name of this
parameter to
[`ingress.sematic_dashboard_url`](https://github.com/sematic-ai/sematic/pull/547)

## FOSS to "Enterprise Edition"[^1]

(0) Reach out to Sematic to obtain a license for "Sematic EE."
(1) In your helm deployment, change `image.repository` to `sematic/sematic-server-ee`.
(2) In your `pip` installation (client installation), change from depending on `sematic`
to `sematic[<extra>]`, where `<extra>` is the appropriate variant of Sematic containing
the EE features you are interested in. See [integrations](#integrations) below for
specific extras. Note that `sematic[all]` will equip clients with ALL Enterprise Edition
features.

## Integrations

### Ray[^1]

Before using this feature, make sure you are set up with a Sematic EE
license. Once that's taken care of, you will need to make the following
changes:

#### Pip package

Instead of depending on `sematic`, you will need to depend on `sematic[ray]`
or `sematic[all]`.

#### Helm chart

Ensure that you are using an [EE server](#foss-to-enterprise-edition1).
Then you will need to install Kuberay into your Kubernetes environment.

##### Installing Kuberay

This can be done via helm, with instructions
[here](https://ray-project.github.io/kuberay/deploy/helm/). Please install the latest
stable version, and not the nightly one! You probably want to use a
`singleNamespaceInstall`  (see
[here](https://github.com/ray-project/kuberay/blob/2600854c61673f2b7da9fe2b54c8220468c1a013/helm-chart/kuberay-operator/values.yaml#L62)) and install it in the same namespace as Sematic. You will probably want to apply
a configuration for a simple ray cluster (such as
[this](https://github.com/ray-project/kuberay/blob/master/ray-operator/config/samples/ray-cluster.complete.yaml))
to verify the deployment. You can delete that cluster once you have verified that the
appropriate pods are created and are marked as ready.

##### Configuring values.yaml

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