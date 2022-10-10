# Developer manual

## Getting started

### Mac OS

Install Bazel:
```shell
$ brew install bazel
```

### Create the dev database

Add the following line to the `.env` file at the root of the
codebase.

```
DATABASE_URL="sqlite3:/$HOME/.sematic/db.sqlite3"
```

Then create the database:

```shell
$ mkdir ~/.sematic
$ touch ~/.sematic/db.sqlite3
```

And run all migrations
```shell
$ bazel run //sematic/db:migrate -- up --verbose
```

## Add third-party pip dependency

Add dependency to `requirements/requirements.in`, and if possible, set a fixed version.

Then run:
```shell
$ python3 -m piptools compile requirements/requirements.in > requirements/requirements.txt --allow-unsafe
```

`--allow-unsafe` is to ensure `setuptools` doesn't get filtered out.

## Build the sematic wheel

```shell
$ bazel build //sematic:sematic_wheel
```

## Generate documentation

```shell
$ sphinx-apidoc -f -o docs/source sematic
$ cd docs
$ make clean
$ make html
```

## Starting the API server

```shell
$ bazel run //sematic/api:server
```

## Starting the UI

```shell
$ cd sematic/ui
$ npm start
```
