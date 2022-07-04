# CLI

Sematic comes with a handy CLI to perform various tasks.

### Start and stop the app

```shell
$ sematic start
```

This command will simply start Sematic's web server locally. It should open a
window in your browser.

To stop the app, simply do

```shell
$ sematic stop
```

### Run examples

Sematic comes with a number of examples out-of-the-box.

To run one do

```shell
$ sematic run examples/mnist/pytorch
```

Since Sematic makes sure not to include unnecessary heavy dependencies, you may
be prompted to install those needed by the example you want to run.


### User settings

Certain Sematic functionalities need certain settings variables to be set. For
example, `SnowflakeTable` needs your Snowflake credentials to be able to query
your data for you.

You can set user settings as follow:

```shell
$ sematic settings set VAR VALUE
```

For example

```shell
$ sematic settings set SNOWFLAKE_USER "foobar"
```

Then you can check your stored settings with

```shell
$ sematic settings show
Active settings:

SNOWFLAKE_USER: foobar
```

These settings are simply store in the `/.sematic/settings.yaml` file on
your machine.

You can always override them at runtime with an environment variable:

```shell
$ SNOWFLAKE_USER="notfoobar" sematic settings show
Active settings:

SNOWFLAKE_USER: notfoobar
```