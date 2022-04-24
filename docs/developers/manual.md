# Developer manual

## Getting started

### Mac OS

Install Bazel:
```shell
$ brew install bazel
```

Install postgres:
```shell
$ brew install postgres
$ /opt/homebrew/bin/createuser -s postgres
```

Install Dbmate:
```shell
$ brew install dbmate
```

### Create the dev database

Add the following line to the `.env` file at the root of the
codebase.

```
DATABASE_URL="postgres://postgres@127.0.0.1:5432/glow_dev?sslmode=disable"
```

Then create the database:

```shell
$ dbmate create
```

And run all migrations
```shell
$ dbmate up
```

## Add third-party pip dependency

Add dependency to `requirements/requirements.in`, and if possible, set a fixed version.

Then run:
```shell
$ python3 -m piptools compile requirements/requirements.in > requirements/requirements.txt --allow-unsafe
```

`--allow-unsafe` is to ensure `setuptools` doesn't get filtered out.

## Build the glow wheel

```shell
$ bazel build //glow:glow_wheel
```