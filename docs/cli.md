# CLI

Sematic comes with a handy CLI to perform various tasks.

### Start and stop the app

```shell
$ sematic start
```

This command will simply start Sematic's web server locally. It should open a
window in your browser.

To stop the app, simply do:

```shell
$ sematic stop
```

### Run examples

Sematic comes with a number of examples out-of-the-box.

To run one do:

```shell
$ sematic run examples/mnist/pytorch
```

Since Sematic makes sure not to include unnecessary heavy dependencies, you may
be prompted to install those needed by the example you want to run.

### User settings

Certain Sematic functionalities need certain settings variables to be set.
These settings control which backend Server will be used when you issue
commands, and other user-specific configurations. For example, `SnowflakeTable`
needs your Snowflake credentials to be able to query your data for you.

You can set user settings as follows:

```shell
$ sematic settings set VAR VALUE
```

For example:

```shell
$ sematic settings set SNOWFLAKE_USER "foobar"
```

Then you can check your stored settings with:

```shell
$ sematic settings show
Active user settings:

SNOWFLAKE_USER: foobar
```

These settings are simply stored in the `~/.sematic/settings.yaml` file on
your machine (the "default" qualifier is a placeholder for a future feature):

```shell
$ cat ~/.sematic/settings.yaml
default:
  SNOWFLAKE_USER: foobar
```

You can always override them at runtime with an environment variable:

```shell
$ SNOWFLAKE_USER="notfoobar" sematic settings show
Active user settings:

SNOWFLAKE_USER: notfoobar
```

If you'd like, you can even change which directory Sematic uses to hold its
settings by setting the environment variable `SEMATIC_CONFIG_DIR`. This can
be either a relative path (it will be treated as relative to your home
directory) or an absolute path.

This is a partial list of supported user settings:
- `SEMATIC_API_ADDRESS`: the address of the Sematic server to use for pipeline
  executions; optional
- `SEMATIC_API_KEY`: the user's personal API key, used to associate pipeline
  submissions; required
- `SNOWFLAKE_USER`: the Snowflake user; required only if you have pipelines
  that use Snowflake
- `SNOWFLAKE_PASSWORD`: the Snowflake password; required only if you have
  pipelines that use Snowflake
- `SNOWFLAKE_ACCOUNT`: the Snowflake account; required only if you have
  pipelines that use Snowflake
- `AWS_S3_BUCKET`: the S3 bucket to use for persisting artifacts; required only
  for cloud pipeline submissions

### Server settings

The same way that certain settings need to be kept on the user side, certain
ones need to configure the backend Server.

The way you configure these depends on how the server you are using is deployed.
If you are using a local server, created with `sematic start`, you can use:

```shell
$ sematic settings set -p sematic.config.server_settings.ServerSettings GRAFANA_PANEL_URL https://grafana.com/
```

These settings are simply stored in the same `~/.sematic/settings.yaml` file on the
machine where the user settings are stored:

```shell
$ cat ~/.sematic/settings.yaml
AWS_S3_BUCKET: XXX
KUBERNETES_NAMESPACE: default
SEMATIC_AUTHORIZED_EMAIL_DOMAIN: XXX
SEMATIC_AUTHENTICATE: 'true'
GOOGLE_OAUTH_CLIENT_ID: XXX
GRAFANA_PANEL_URL: XXX
```

They can also be overridden via environment variables, just like the user
settings. If you have deployed your Sematic server in a Docker container, environment
variables are the preferred way to configure it.

This is a partial list of supported server settings:
- `SEMATIC_AUTHENTICATE`: whether to require authentication on API calls;
  optional
- `SEMATIC_AUTHORIZED_EMAIL_DOMAIN`: the email domain that is allowed to create
  accounts in the UI; optional
- `SEMATIC_WORKER_API_ADDRESS`: the address of the remote cloud worker API,
  such as the Kubernetes API; optional; if set, this should be set to the DNS
  location of the Sematic service within Kubernetes
- `SEMATIC_DASHBOARD_URL`: the address that will be used to construct links
  to locations in the dashboard (ex: in log outputs).
- `GOOGLE_OAUTH_CLIENT_ID`: the Google OAuth client ID to use for
  authentication; optional
- `GITHUB_OAUTH_CLIENT_ID`: the GitHub OAuth client ID to use for
  authentication; optional
- `GRAFANA_PANEL_URL`: the URL of the Grafana deployment that tracks jobs
  details

There are other settings which are only relevant in the case that you have done
a helm deployment of Sematic. For these configurations, please refer to our
(helm docs)[https://sematic-ai.github.io/helm-charts/sematic-server/].
Note that those docs also provide ways to configure the settings above via helm,
which is preferred for helm deployments.

### Cancel pipelines

You can cancel pipelines using the `cancel` command:

```shell
$ sematic cancel <run-id>
```

where `run-id` is the ID of any run in the pipeline. You can get this ID from
the console logs, or from the UI.

Note that all unfinished runs in the pipeline will be canceled.
