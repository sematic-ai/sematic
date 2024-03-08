# Developer Docs
This directory contains documentation for people working on/developing Sematic
itself. Documents intended for users of Sematic are in the `docs` directory,
and are published to https://docs.sematic.dev/

## Setup

The developer tools need to be installed by running this command once (and subsequently
whenever `requirements/ci-requirements.txt`) will be updated:
```bash
$ make install-dev-deps
```

### Bazel installation

Be sure to install a compatible version of bazel: `sudo apt update && sudo apt install bazel-6.1.1`

You may also want to add the following to your .bashrc: `export USE_BAZEL_VERSION=6.1.1`

## Testing

Guideline for testing changes that might impact pipeline runs:
- the CI tests must pass
- test locally
- test remotely in non-detached mode
- test remotely in detached mode

## PR Prerequisites

In order to ensure the PR review goes swiftly, please:

- Add a comprehensive description to your PR
- Ensure your code is properly formatted and type checked
  - Make sure you have the dev tools installed by running `make install-dev-deps` (you only ever need to do this once)
  - Use `make pre-commit` to run the linter and code formatter
  - Use `make update-schema` to make sure any DB changes you made are accounted for
- Make sure the CircleCI build passes for your branch (linked in the checks section at the bottom of the GitHub PR page)
- Add `sematic-ai/staff` as a reviewer, but also try to assign a specific reviewer, such as `neutralino1`

## Switching profiles

The [user settings](../docs/cli.md#user-settings) are saved to the
`~/.sematic/settings.yaml` files, under the "default" entry. Example:

```bash
$ cat ~/.sematic/settings.yaml
default:
  SEMATIC_API_ADDRESS: http://127.0.01:5001
  SEMATIC_API_KEY: XXX
```

These are accessible through the CLI commands for more user-friendliness:

```bash
$ sematic settings show
Active user settings:

SEMATIC_API_ADDRESS: http://127.0.0.1:5001
SEMATIC_API_KEY: <my_local_api_key>
```

When developing, we often need to switch the Server where we submit pipelines,
sometimes bundled together with other settings as well. In order to avoid
constantly editing this file manually, we can define one file per environment
or profile, under the names `~/.sematic/settings.yaml.<profile>`, and switch
between them using `bazel run //tools:switch-settings -- <profile>`.

This actually copies these profile files over the main settings file. Example:

```bash
$ bazel run //tools:switch-settings -- prod1
[...]
Copying previous settings to /Users/tudorscurtu/.sematic/settings.yaml_bck
Copying /Users/tudorscurtu/.sematic/settings.yaml.prod1 to /Users/tudorscurtu/.sematic/settings.yaml

Successfully switched to prod1!

$ sematic settings show
Active user settings:

SEMATIC_API_ADDRESS: https://<my_prod1_host:port>
SEMATIC_API_KEY: <my_prod1_api_key>
```

## Building the Wheel

If you want to build the wheel from source, do:

```bash
$ make ui
$ make wheel
```

## SQLite vs Postgres Migrations

When modifying existing tables in the database, there are some important differences in
the types of operations that are supported by SQLite, and so care must be taken to ensure
that the migration works for both types of databases.

[SQLite ALTER TABLE docs] (https://www.sqlite.org/lang_altertable.html) explain this well.

If your PR does need to perform database-specific migrations, you can use one of the
existing migrations in `sematic/db/migrations` that do this as a reference.  All PRs that
are affected by the table modification incompatibilities *must* resolve the issue in this
manner.

## Releasing

**Note:** Actually pushing the artifacts and accessing some of the repositories listed in
this section can only be done if you have access to the PyPI repo, which is limited to
employees of Sematic.

We cut releases from the `main` branch, following the steps below. They must be
performed in order, without skipping any. If any errors occur, you must fix
them and then go back and redo all the steps that have been affected by the
changes.

1. Announce internally that a `main` merge freeze has started.

1. Bump the version in:
   - `wheel_constants.bzl` - `wheel_version_string`
   - `helm/sematic-server/Chart.yaml` - `appVersion`
   - `sematic/versions.py` - `CURRENT_VERSION`; bump `MIN_CLIENT_SERVER_SUPPORTS` if
     there are any TODOs mentioning this should be done
   - `./README.md` - PyPI badge

1. Increment the patch version of the `version` field in
  `helm/sematic-server/Chart.yaml`. Note that this will be DIFFERENT
  from the Sematic version you changed in prior steps (chart version
  will be `1.X.Y`, Sematic version is `0.M.N`).

1. Update `changelog.md` with the new version number and any missing change entries.

1. Build the UI:
    ```bash
    $ make ui
    ```

1. Build the wheel:
    ```bash
    $ make wheel
    ```

1. Test the Server wheel locally for all supported versions of Python.

    1. Copy the wheel from `bazel-bin/sematic/sematic-*.whl` into a scratch
    directory.

    1. For each supported version of Python, use a virtual env to test:
      ```bash
      $ # LOCALLY:
      $ pip3 install <wheel path>
      $ sematic stop
      $ sematic version # check that the correct sematic and python versions are used
      $ sematic start
      $ sematic run examples/mnist/pytorch
      $ sematic stop
      ```

1. Test the [internal Helm charts](/helm/sematic-server) deployment.

    1. **Test an upgrade deployment** in the `stage` environment, **where the previous
    version is already deployed**, use
    [`serve-dev`](https://github.com/sematic-ai/infrastructure/tree/main/bin) to upgrade
    the deployment with a Docker image built on-the-fly from the current release commit.
    You must set `BUILD_UI=1` in the `me.sh` script in order to ensure the UI is built, so
    you don't package an older version of the UI with the deployment:
        ```bash
        $ vim ~/infrastructure/bin/me.sh  # add: BUILD_UI=1 at the end
        $ # STAGE:
        $ serve-dev stage
        $ helm list -n stage  # check that the expected APP VERSION was deployed
        ```

    1. Smoke test new features that were included or significantly updated in the
    release.

    1. Ensure you have a compatible version of bazel:

      ```bash
      $ export USE_BAZEL_VERSION=6.1.1
      $ sudo apt update && sudo apt install bazel-6.1.1
      ```

    1. Run the Testing Pipeline with the test cases listed below on this deployment, and
      check that it completes successfully, while perusing its outputs and logs to check
      that they render correctly.
      
        ```bash
        $ # STAGE:
        $ bazel run sematic/examples/testing_pipeline:__main__ -- \
              --cloud \
              --detach \
              --max-parallelism 10 \
              --inline \
              --nested \
              --no-input \
              --sleep 10 \
              --spam-logs 1000 \
              --fan-out 10 \
              --raise-retry 0.7 \
              --external-resource \
              --expand-shared-memory \
              --mount-host-path /tmp /test \
              --mount-host-path /tmp /test2 \
              --cache-namespace test \
              --images \
              --virtual-funcs \
              --fork-subprocess return 0 \
              --fork-subprocess exit 0 \
              --fork-subprocess exit 1 \
              --fork-subprocess signal 2 \
              --fork-subprocess signal 15
        ```

    1. Test client backwards compatibility. Install the version of Sematic that matches
    `MIN_CLIENT_SERVER_SUPPORTS` from `sematic/versions.py` in a virtual env and validate
    that this older client can run a packaged example pipeline end-to-end successfully on
    the new Server.
        ```bash
        $ sematic version #  check that the correct min version is installed
        $ STAGE:
        $ sematic run examples/mnist/pytorch
        ```

    1. **Test a clean installation** in the same `stage` environment.
        ```bash
        $ # STAGE:
        $ helm uninstall sematic-server -n stage
        $ helm list -n stage  # check that the chart was uninstalled
        $ serve-dev stage
        $ helm list -n stage  # check that the expected APP VERSION was deployed
        ```

    1. Wait a few minutes for AWS to bootstrap the services and network configuration.
    Smoke test that a simple pipeline succeeds, this time in local mode, to cover that
    aspect as well.
        ```bash
        $ # STAGE:
        $ bazel run sematic/examples/testing_pipeline:__main__
        ```

1. Test publishing the wheel. Check if the generated webpage on `test.pypi.org` is
  rendered correctly.
    ```bash
    $ make test-release
    ```

1. Make the release PR, containing all version changes and required fixes for issues
  discovered during validation. Even the previous step compiled documentation changes
  that must be included. After implementing comments and getting approval on the release
  PR, merge it and pull from the updated `main` branch. **It is mandatory to include this
  updated version of `main` in the subsequent steps.**

1. Publish the wheel. Check if the generated webpage on `pypi.org` is rendered correctly.
    ```bash
    $ make release
    ```

  If you have 2FA enabled for your account, you need to use an API token as password and 
  `__token__` as username when prompted by the CLI for credential. To set up a `pypi.org` 
  API token, go to "Account Settings" -> "API tokens". 

  Instead of manually typing the username and password, one can also edit `~/.pypirc`, adding 
  below:
    ```
      [pypi]
      username = __token__
      password = <the token>
    ```    

1. Add the git tag.
    ```bash
    $ export RELEASE_VERSION=v$(python3.9 ./sematic/versions.py)
    $ git tag $RELEASE_VERSION
    $ git push origin $RELEASE_VERSION
    ```

1. Announce internally that the `main` merge freeze is over.

1. Build and push the Server Docker image. Use the Dockerfile at
  `docker/Dockerfile.server`.
    ```bash
    $ TAG=v$(python3.9 ./sematic/versions.py) make release-server
    ```

2. Next you can generate the Helm package and publish it to the Helm repository.

    1. `[First time setup]` Clone the repo with
      `git clone git@github.com:sematic-ai/helm-charts.git`, and check out the `gh-pages`
      branch in it. The commands below assume the `helm-charts` repo has been cloned into
      the `~/code/helm-charts` directory, but they should be run from the root of the
      `github.com/sematic-ai/sematic` repo directory.

    1. Make sure your `helm-charts` project's `gh-pages` branch is up-to-date.
        ```bash
        $ cd ~/code/helm-charts
        $ git checkout gh-pages
        $ git pull
        $ cd ~/code/sematic
        ```

    1. Generate the updated Helm package from the Sematic repo.
        ```bash
        $ export HELM_REPO=~/code/helm-charts
        $ helm package helm/sematic-server
        $ helm repo index . \
                --url https://sematic-ai.github.io/helm-charts/sematic-server \
                --merge $HELM_REPO/index.yaml
        $ mv index.yaml $HELM_REPO/index.yaml
        $ mv *.tgz $HELM_REPO/sematic-server/
        ```

    1. (OPTIONAL) Only do this step if you know that the Sematic Grafana dashboards
    have been updated and need to be released.  Generate the updated Helm package
    from the Sematic repo.
        ```bash
        $ export HELM_REPO=~/code/helm-charts
        $ helm package helm/sematic-grafana-dashboards
        $ helm repo index . \
                --url https://sematic-ai.github.io/helm-charts/sematic-grafana-dashboards \
                --merge $HELM_REPO/index.yaml
        $ mv index.yaml $HELM_REPO/index.yaml
        $ mv *.tgz $HELM_REPO/sematic-grafana-dashboards/
        ```

    1. You should now have a new `sematic-server/sematic-server-X.X.X.tgz` file in the
    `helm-charts` repo, and a modified `index.yaml` file. If you optionally created a package
    for the Grafana dashboards, you should also have a
    `sematic-grafana-dashboards/sematic-grafana-dashboards-X.X.X.tgz` file in the `helm-charts`
    repo.  Commit and push all of these to a new release branch, and create a PR for the change
    based on `gh-pages`. Wait for approval, and merge it.

1. Deploy this new official release to the `stage` environment, in order to leave it in a
  consistent and expected state, and to test the actual commands users will be using to
  deploy the release.
    ```bash
    $ # Run this step if it has never been done before
    $ helm repo add sematic-ai https://sematic-ai.github.io/helm-charts

    $ # STAGE:
    $ helm repo update
    $ helm upgrade sematic-server sematic-ai/sematic-server -n stage -f /path/to/stage_values.yml
    $ helm list -n stage  # check that the expected APP VERSION was deployed
    ```

1. Finally, draft the release on GitHub, from
  [the tag you previously committed](https://github.com/sematic-ai/sematic/tags):
    - Pick the `"previous tag"` from the dropdown to refer to the previous release.
    - Add a `"## What's Changed"` section, and copy the newly added section of the
      `changelog.md`.
    - Add a `"Full Changelog"` link, and validate it.
    - Add a `"# Helm Chart Version` section, and list the `appVersion` field here from
      `helm/sematic-server/Chart.yaml`.
    - Add a `"## Compatibility"` section which states that only clients versions down to
      `MIN_CLIENT_SERVER_SUPPORTS` from `sematic/versions.py` are supported.
    - If `docs/upgrades.md` contains an entry for upgrading to the released version, add
      an `"## Upgrade Instructions"` section, and list and link this documentation entry.
    - Add a `"## New Contributors"` section, if this applies. List all external
      contributors who have made commits since the last release, and thank them.
    - Attach the wheel in the `"Assets"` section.

### Patch Releases

If an issue is discovered on the latest release which impacts users to an extent that
warrants a hotpatch, then instead of performing the release from the `main` branch, we:
- create a separate hotpatch release branch starting from the previous release tag and
  switch to that branch
- fix the issue and merge it into the release branch via either the normal PR review
  procedure, or by merging directly in time sensitive situations
- follow all the other steps from the [Releasing](#releasing) section
- switch to the `main` branch, cherry-pick all the changes contained in the hotpatch
  branch, and merge a PR with these commits

### Special Releases

Sometimes we want to cut releases that contain only a subset of changes that
have been included in the `main` branch since the previous release. In these
cases, instead of performing the release from the `main` branch, we:
- create a separate release branch starting from the previous release tag and
  switch to that branch
- cherry-pick the commits we want to include
- follow all the other steps from the [Releasing](#releasing) section
- switch to the `main` branch, make a commit that contains the previous version
  increase and reconciles the changelog, and merge a PR with this commit

## Updating the CircleCi Image

The image used for most of our CircleCi steps is built using `docker/Dockerfile.ci`.
After updating it, open a PR with the change, push the image to Dockerhub using the PR
number as a tag (in order to be able to maintain a history, and revert, if necessary),
and update the `SEMATIC_CI_IMAGE` env var in the CircleCi project settings.
