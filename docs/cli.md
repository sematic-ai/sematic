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
your machine.

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

### Server settings

The same way that certain settings need to be kept on the user side, certain
ones need to configure the backend Server.

These can be accessed and modified just like the user settings, but by using
the `sematic server-settings` command instead:

```shell
$ sematic server-settings show
Active server settings:

AWS_S3_BUCKET: XXX
KUBERNETES_NAMESPACE: default
SEMATIC_AUTHORIZED_EMAIL_DOMAIN: XXX
SEMATIC_AUTHENTICATE: 'true'
GOOGLE_OAUTH_CLIENT_ID: XXX
GRAFANA_PANEL_URL: XXX

```

These settings are simply stored in the `~/.sematic/server.yaml` file on the
machine which needs to start a backend Server. They can also be overridden via
environment variables.

### Cancel pipelines

You can cancel pipelines using the `cancel` command:

```shell
$ sematic cancel <run-id>
```

where `run-id` is the ID of any run in the pipeline. You can get this ID from
the console logs, or from the UI.

Note that all unfinished runs in the pipeline will be canceled.
