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

This is the full list of supported user settings:
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
- `AWS_S3_ENDPOINT_URL`: the S3 endpoint url; required only if you are using 
  an object storage service that is not AWS S3 but compatible with the S3 protocol

### Server settings

The same way that certain settings need to be kept on the user side, certain
ones need to configure the backend Server.

These can be accessed and modified just like the user settings, but by using
the `sematic server-settings` command instead:

```shell
$ sematic server-settings show
Active server settings:

KUBERNETES_NAMESPACE: default
SEMATIC_AUTHORIZED_EMAIL_DOMAIN: XXX
SEMATIC_AUTHENTICATE: 'true'
GOOGLE_OAUTH_CLIENT_ID: XXX
GRAFANA_PANEL_URL: XXX

```

These settings are simply stored in the `~/.sematic/server.yaml` file on the
machine which needs to start a backend Server (this file does not have the
settings nested under a "default" entry):

```shell
$ cat ~/.sematic/server.yaml
AWS_S3_BUCKET: XXX
KUBERNETES_NAMESPACE: default
SEMATIC_AUTHORIZED_EMAIL_DOMAIN: XXX
SEMATIC_AUTHENTICATE: 'true'
GOOGLE_OAUTH_CLIENT_ID: XXX
GRAFANA_PANEL_URL: XXX
```

They can also be overridden via environment variables, just like the user
settings.

This is the full list of supported server settings:
- `SEMATIC_AUTHENTICATE`: whether to require authentication on API calls;
  optional
- `SEMATIC_AUTHORIZED_EMAIL_DOMAIN`: the email domain that is allowed to create
  accounts in the UI; optional
- `SEMATIC_WORKER_API_ADDRESS`: the address of the remote cloud worker API,
  such as the Kubernetes API; optional; if set, this should be set to the DNS
  location of the Sematic service within Kubernetes
- `GOOGLE_OAUTH_CLIENT_ID`: the Google OAuth client ID to use for
  authentication; optional
- `GITHUB_OAUTH_CLIENT_ID`: the GitHub OAuth client ID to use for
  authentication; optional
- `KUBERNETES_NAMESPACE`: the namespace to use for Kubernetes jobs; required
  only for cloud pipeline submissions
- `GRAFANA_PANEL_URL`: the URL of the Grafana deployment that tracks jobs
  details

### Cancel pipelines

You can cancel pipelines using the `cancel` command:

```shell
$ sematic cancel <run-id>
```

where `run-id` is the ID of any run in the pipeline. You can get this ID from
the console logs, or from the UI.

Note that all unfinished runs in the pipeline will be canceled.
