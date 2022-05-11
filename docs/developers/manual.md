# Developer manual

## Getting started

### Mac OS

Install Bazel:
```shell
$ brew install bazel
```

Install Dbmate:
```shell
$ brew install dbmate
```

### Create the dev database

Add the following line to the `.env` file at the root of the
codebase.

```
DATABASE_URL="sqlite3:/$HOME/.glow/db.sqlite3"
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

## Generate documentation

```shell
$ sphinx-apidoc -f -o docs/source glow
$ cd docs
$ make clean
$ make html
```

## Starting the API server

```shell
$ bazel run //glow/api:server
```