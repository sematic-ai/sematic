# Upgrades

This page contains some guidance on upgrading an existing deployment of Sematic
in various circumstances.

## General guidance

Sematic has 3 versioned entities, depending on your usage:

- **pip package**: If you are using Sematic only locally, this is
the only versioned entity you need. This determines the code
that will be used for your code to interact with the server,
including how Sematic resolvers interact with the server.
- **Server**: If you are using Sematic in the cloud, you need this
and the pip package.
- **bazel integration**: If you are using `bazel` with Sematic, you
need this versioned entity as well.

When you are upgrading Sematic, you generally want to upgrade all of
the versions you are using at the same time. It is impossible to
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

For purposes of this discussion, "client" generally refers to
the code installed with your pip package, which applies to how your
source code interacts with the Server API via our SDK, including
how remote resolution jobs interact with that Server API.

You will always want to upgrade the server before upgrading the pip package.
If the server is being upgraded to a version that still supports the version being
used by your clients, you can often upgrade the server without any downtime for
users. This is one benefit of keeping up-to-date with regular upgrades! If you
want to know what client versions a given server supports, you can look at
the [release notes](https://github.com/sematic-ai/sematic/releases).

Often, you will need to upgrade the server beyond support for the clients
currently in use. When this happens, an example upgrade workflow would be:

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

{% hint style="info" %}
This section contains instructions for migrating from one
version of Sematic to another. It does not cover every version
delta, but only:

(a) from one version to a subsequent one
(b) upgrades where there are non-trivial details to pay attention to
when performing the upgrade.
{% endhint %}

### v0.25.X to v0.26.Y

#### Dependency changes

As a part of adding python 3.10 support, Sematic has changed
from depending on `eventlet` to depending on `gevent`. If you
use requirements locking systems like [Poetry](https://python-poetry.org/)
or [pip-tools/pip-compile](https://pypi.org/project/pip-tools/)
you will need to regenerate your dependency lockfiles.

#### Bazel API changes

The `image_layers` field in `sematic_pipeline` bazel macro
now ONLY gets passed to image layering, and not also to the Sematic binary target.
if you are using `image_layers` to express dependencies of a pipeline, you will now
need to duplicate them in the `deps` field.

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

## FOSS to "Enterprise Edition"

0. Reach out to Sematic via support@sematic.dev to obtain a license for "Sematic EE."
1. In your helm deployment, change `image.repository` to `sematic/sematic-server-ee`.
2. In your `pip` installation (client installation), change from depending on `sematic`
to `sematic[<extra>]`, where `<extra>` is the appropriate variant of Sematic containing
the EE features you are interested in. See [integrations](#integrations) below for
specific extras. Note that `sematic[all]` will equip clients with ALL Enterprise Edition
features.

## Integrations

Some integrations require changes to how pip packages and Helm deployments
are installed and configured:

- [Ray](./ray.md)
