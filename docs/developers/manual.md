# Developer manual

## Getting started

## Build System

Install Bazel:
- [MacOS](https://bazel.build/install/os-x#install-on-mac-os-x-homebrew)
- [Ubuntu](https://bazel.build/install/ubuntu#install-on-ubuntu)
- [RHEL](https://bazel.build/install/redhat)

## Dev Tools

```shell
$ make install-dev-deps
```

## Add a third-party pip dependency

Add your dependency to `requirements/requirements.in`. Avoid pinning a fixed version unless necessary.

Then run (only supported on Linux):
```shell
$ make refresh-dependencies
```

## Starting the API server

```shell
$ bazel run //sematic/api:server
```

## Starting the UI Dashboard

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

## Building the Sematic Wheel

This is if you want to package a dev Sematic version for installation somewhere else:

```shell
$ make install-dev-deps  # if not done before
$ make ui
$ make wheel
```