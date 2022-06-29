# Snowflake integration

Sematic tries to provide easier ways for you to access your data.

If your data is sitting in a Snowflake Data Warehouse, you can use these tools
to access it.

## Set your Snowflake credentials

In a console do

```
$ sematic credentials set snowflake SNOWFLAKE_USER "foobar"
$ sematic credentials set snowflake SNOWFLAKE_PASSWORD "foobar"
$ sematic credentials set snowflake SNOWFLAKE_ACCOUNT "foobar"
$ sematic credentials show
snowflake:
    SNOWFLAKE_USER: foobar
    SNOWFLAKE_PASSWORD: foobar
    SNOWFLAKE_ACCOUNT: foobar
```

These credentials are simply store in the `/.sematic/credentials.yaml` file on
your machine.

## `SnowflakeTable` type

One you have set your credentials, use the `SnowflakeTable` type.

```
>>> from sematic.types.types.snowflake import SnowflakeTable
>>> table = SnowflakeTable(database="my_database", table="my_table")
>>> df = table.to_df(limit=500)
>>> len(df)
500
```

## `SnowflakeQuery` type

Coming soon.
