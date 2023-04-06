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

## Diagnose UI Dashboard issues

The local development server launched by [Create-React-Apps](https://create-react-app.dev/) is set up by default to provide extensive logging, which is helpful for investigating issues with the front-end. However, this logging is disabled by default for production builds.

If you need to enable excessive logging in a production build, you can add "debug=true" as a query parameter to any dashboard page (being careful not to add it after URL hashes). Once you've set this parameter, it will be remembered even if you don't explicitly include it in the URL. This means that the debug state will be maintained even after page refreshes.

To turn off excessive logging, you can append debug=false to the URL again, or you can clear it from localStorage using browser developer tools. 


## Starting Storybook to browse UI components

```shell
$ cd sematic/ui
$ npm run storybook
```
