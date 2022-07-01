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


### Set credentials

Certain integrations need credentials. `SnowflakeTable` needs your Snowflake
credentials to be able to query your data for you.

You can set credentials as follow:

```shell
$ sematic credentials set APP VAR VALUE
```

For example

```shell
$ sematic credentials set snowflake SNOWFLAKE_USER "foobar"
```

Then you can check every thing is alright with

```shell
$ sematic credentials show
Active credentials:

snowflake:
  SNOWFLAKE_USER: foobar
```