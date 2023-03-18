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

## Testing

Guideline for testing changes that might impact resolution:
- the CI tests must pass
- test locally
- test remotely in non-detached mode
- test remotely in detached mode

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

If you want to build the wheel from sources, do:

```bash
$ make ui
$ make wheel
```

## Releasing

**Note:** Actually pushing the released wheel can only be done if you have
access to the PyPi repo, which is limited to employees of Sematic.

We cut releases from the `main` branch, following the steps below. They must be
performed in order, without skipping any. If any errors occur, you must fix
them and then go back and redo all the steps that have been affected by the
changes.

1. Bump the version in:
   - `wheel_constants.bzl` - `wheel_version_string`
   - `helm/sematic-server/Chart.yaml` - `appVersion`
   - `sematic/versions.py` - `CURRENT_VERSION`; bump
     `MIN_CLIENT_SERVER_SUPPORTS` if there are any TODOs mentioning this should
     be done
   - `./README.md` - PyPI badge

1. Increment the minor version of the `version` field in
  `helm/sematic-server/Chart.yaml`. Note that this will be DIFFERENT
  from the Sematic version you changed in prior steps (chart version
  will be `1.X.Y`, Sematic version is `0.M.N`).

1. Update `changelog.md` with the new version number and any missing change
  entries

1. Make the release PR, containing the previous changes. After implementing
  comments and getting approval on the release PR, merge it and pull from the
  updated `main`. It is mandatory to include this version of main in the
  subsequent steps. If validation issues are discovered, they must be fixed
  in patch PRs, and the process restarted from this step.

1. Build the UI:
  ```bash
  $ make ui
  ```

1. Build the wheel:
  ```bash
  $ make wheel
  ```

1. Copy wheel from `bazel-bin/sematic/sematic-....whl` into a scratch
  directory, and use a virtual env to test:

  ```bash
  $ pip3 install <wheel path>
  $ sematic stop
  $ sematic start
  $ sematic run examples/mnist/pytorch
  $ sematic stop
  ```

  Do this for all supported versions of Python. You can check your virtual env
  Python version using `sematic version` (as well as the Server and Client
  version).

1. At this point, you should also deploy the Docker image to a cloud Dev environment
  using the [internal Helm charts](/helm/sematic-server), and execute at least one
  pipeline in detached cloud mode. To build the image, use the same process
  you do when usually deploying dev code to a dev env. You can use
  [`serve-dev`](https://github.com/sematic-ai/infrastructure/tree/main/bin)
  to build and deploy the image while on the release branch to deploy the
  release candidate. You will likely also want to smoke test new features
  that were included in the release.

1. Run the Testing Pipeline with "the works" on this deployment, and check that
  it completes successfully, while perusing its outputs and logs to check they
  render correctly:
  ```bash
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
        --cache-namespace test \
        --images \
        --virtual-funcs \
        --fork-subprocess return 0 \
        --fork-subprocess exit 0 \
        --fork-subprocess exit 1 \
        --fork-subprocess signal 2 \
        --fork-subprocess signal 15
  ```

1. Test publishing the wheel. Check if the generated webpage is rendered
  correctly.
  ```bash
  $ make test-release
  ```

1. Publish the wheel. Check if the generated webpage is rendered
  correctly.
  ```bash
  $ make release
  ```

1. Add the git tag.
  ```bash
  $ export RELEASE_VERSION=v$(python3 ./sematic/versions.py)
  $ git tag $RELEASE_VERSION
  $ git push origin $RELEASE_VERSION
  ```

1. Build and push the Server Docker image. Use the Dockerfile at
  `docker/Dockerfile.server`.
  ```bash
  $ TAG=v$(python3 sematic/versions.py) make release-server
  ```

1. Next you can generate the Helm package and publish it to the Helm repository.
  Clone the repo with `git clone git@github.com:sematic-ai/helm-charts.git`, and
  check out the `gh-pages` branch in it.  The commands below assume the
  `helm-charts` repo has been cloned into the `~/code/helm-charts` directory,
  but they should be run from the root of the `github.com/sematic-ai/sematic`
  repo directory.
  ```bash
  $ export HELM_REPO=~/code/helm-charts
  $ helm package helm/sematic-server
  $ helm repo index . --url https://sematic-ai.github.io/helm-charts/sematic-server \
           --merge $HELM_REPO/index.yaml
  $ mv index.yaml $HELM_REPO/index.yaml
  $ mv *.tgz $HELM_REPO/sematic-server/
  ```

  You should now have a new `sematic-server/sematic-server-X.X.X.tgz` in the
  `helm-charts` repo, and a modified `index.yaml`.  Commit and push both of
  these to a new branch, and create a PR for the change based on `gh-pages`
  necessary.

1. Finally, draft the release on GitHub:
   - Pick the "previous tag" from the dropdown.
   - Add a "What's Changed" section.
   - If `MIN_CLIENT_SERVER_SUPPORTS` was bumped and/or if `docs/upgrades.md`
     contains an entry for upgrading to the released version, add an
     "Upgrade Instructions" section and list and link all these steps
   - Add a "New Contributors" section, if this applies.
   - Add a "Full Changelog" link.
   - Attach the wheel in the "Assets" section.

### Special Releases

Sometimes we want to cut releases that contain only a subset of changes that
have been included in the `main` branch since the previous release. In these
cases, instead of performing the release from the `main` branch, we:
- create a separate release branch starting from the previous release tag and
  switch to that branch
- cherry-pick the commits we want to include
- follow all the other steps from the [Releasing](#releasing) section
- switch to the `main` branch, make a commit that contains the previous version
  increases and reconciles the changelog, and merge a PR with this commit
