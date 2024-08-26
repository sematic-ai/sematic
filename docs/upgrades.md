# Upgrades

This page contains some guidance on upgrading an existing deployment of Sematic
in various circumstances.

## General guidance

Sematic has 3 versioned entities, depending on your usage:

- **pip package**: If you are using Sematic only locally, this is
the only versioned entity you need. This determines the code
that will be used for your code to interact with the server,
including how Sematic runners interact with the server.
- **Server**: If you are using Sematic in the cloud, you need this
and the pip package.
- **bazel integration**: If you are using `bazel` with Sematic, you
need this versioned entity as well.

When you are upgrading Sematic, you generally want to upgrade all of
the versions you are using at the same time. It is impossible to
upgrade all of them literally atomically, so we recommend upgrading in
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
helm repo update
helm upgrade sematic-server -f /path/to.values.yaml
```

## Upgrading the server past supported client versions

For purposes of this discussion, "client" generally refers to
the code installed with your pip package, which applies to how your
source code interacts with the Server API via our SDK, including
how remote runner jobs interact with that Server API.

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

### vX.X.X to v0.39.0

In v0.39.0, Sematic switched its [SQLAlchemy](https://www.sqlalchemy.org/)
dependency from a pre 2.0 version to a post 2.0 version. SQLAlchemy introduced
breaking changes in 2.0, so if you arte using Sematic in a python environment
that depends on SQLAlchemy <2.0 (even transiently), you will need to upgrade
your code and its dependencies to use SQLAlchemy >=2.0 before upgrading
to or past this version of Sematic. If you need to know what changes to
make to your own code, a migration guide can be found
[here](https://docs.sqlalchemy.org/en/20/changelog/migration_20.html)

### vX.X.X to v0.35.0

In v0.35.0 support for deploying Sematic with a combined API and SocketIO server
was removed. Most users deploy with a dedicated SocketIO server anyway, in which
case this change does not impact you. You may still want to remove the
`deployment.socket_io.dedicated` configuration from your helm values, as it will
now be ignored.

The default for the helm configuration `service.create` was changed to `true` as
well. Again, most users have this set to `true` in which case it does not impact
you. If you were relying on the default to be `false` so you could create your
own Kubernetes service object for Sematic, you now must explicitly set
`service.create` to `false` in your helm values.

If you were using a non-dedicated SocketIO deployment (`deployment.socket_io.dedicated`
set to `false`, or unspecified), you must now adopt the new setup with dedicated API and
SocketIO servers. You must first uninstall the old deployment, and then deploy the updated
charts, because a direct upgrade will fail.
 
### vX.X.X to v0.32.0

In v0.32.0 new constraints were added to the schema of the database that
maintains Sematic's data model, in order to improve validations and data
consistency. In case your database contains corrupt entries (due to unknown and
unforeseen errors), the upgrade to v0.32.0 might fail with an error message. If
this happens, please contact us on [Discord](https://discord.gg/4KZJ6kYVax) and
share the error details, so we can help you with the upgrade.

This version also comes with a new version of the Dashboard UI, which is
currently in "Beta". You can switch to it by clicking on the banner that pops
up when opening the old version of the Dashboard, or by selecting the new
version from your profile icon pop-up in the bottom-left of the old version of
the Dashboard. You can switch back the same way, only now the profile icon is
located in the top-right of the new Dashboard.

In order to improve the clarity of the concepts in our architecture, the "Resolver" term
was renamed to "Runner". Also, now when executing a pipeline `Future`, you need to
explicitly pass it to a specific `Runner`, instead of relying on a default one. There
will be a deprecation period of two releases in which both API versions will still be
supported, but you should consider performing this migration in your code soon:

You need to update your code which looks like this:
```python
my_future = my_pipeline([...])

my_future.resolve()
# or:
my_future.resolve(CloudResolver([...]))
# or:
my_future.resolve(LocalResolver([...]))
# or:
my_future.resolve(SilentResolver([...]))
```

To this:
```python
my_future = my_pipeline([...])

my_runner = CloudRunner([...])
# or:
my_runner = LocalRunner([...])
# or:
my_runner = SilentRunner([...])

my_runner.run(my_future)
```

### <v0.30.0 to v0.31.0

Normally Sematic tries to preserve a server/client compatibility support window
of at least two releases. In other words, a client at release `N` should be able
to execute against a server at release `N+2`. However, for this release the
server can only support clients at v0.30.0 (the previous release). 

The python webserver running on Kubernetes has also changed (from gunicorn to
uvicorn), which has increased the startup latency for new server pods.

### vX.X.X to v0.30.0

Default Kubernetes deployments of the Sematic server will now run with 2 pods
for the API server, in order to enable high availability.  As such, the memory
and CPU requests and limits for each pod has been halved.

Sematic clients at versions <v0.30.0 may break when used with the server at
version 0.30.0, so it is recommended that you follow the procedure described
in
[Upgrading the server past supported client versions](#upgrading-the-server-past-supported-client-versions)
when deploying this release.

### v0.28.X to v0.29.0

Direct support for Matplotlib figures was dropped in favor of the [`Image`
type](./types.md#the-image-type).

### v0.27.0 to v0.28.0

**Important!**: Any in-progress runs will fail when the server is upgraded.
Please perform this upgrade at a time when there are no runs or where failures
are acceptable.

As of this release, the minimum supported Kubernetes version has been changed to >1.23.
Non supported versions *may* continue to work, but are not validated. Please upgrade
your Kubernetes if you are on an older version.

### v0.26.X to v0.27.Y

#### Helm chart changes

A new `bucket_region` value needs to be set in the deployment Helm chart:

```yaml
aws:
  enabled: true
  storage_bucket: my-s3-bucket # REPLACE ME
  bucket_region: my-s3-region # REPLACE ME

```

#### Dependency changes

As a part of adding python 3.10 support, Sematic has changed
from depending on `eventlet` to depending on `gevent`. If you
use requirements locking systems like [Poetry](https://python-poetry.org/)
or [pip-tools/pip-compile](https://pypi.org/project/pip-tools/)
you will need to regenerate your dependency lockfiles.

The new [`Image`](types.md#the-image-type) type now requires the `libmagic` system
library. If you want to use `Image`, please install that dependency by following
[these instructions](get-started.md#system-dependencies).

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

0. Reach out to Sematic via [support@sematic.dev](mailto:support@sematic.dev) to obtain
an Enterprise License.
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
