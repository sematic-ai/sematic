# Developer Docs
This directory contains documentation for people working on/developing Sematic
itself. Documents intended for users of Sematic are in the `docs` directory,
and are published to https://docs.sematic.dev/

## Setup

The developer tools need to be installed by running this command once (and
subsequently whenever `requirements/ci-requirements.txt`) will be updated:
```bash
$ make install-dev-deps
```

## Development

Simple issues can be self-contained inside PRs. Issues that implement or
partially implement reported
[issues](https://github.com/sematic-ai/sematic/issues) must reference that
issue in the PR description.

Large features or refactorings must come with a design which has gone through
the process described
[here](https://github.com/sematic-ai/sematic/tree/main/developer-docs/designs/README.md).

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

## Releasing

**Note:** Actually pushing the released wheel can only be done if you have
access to the PyPi repo, which is limited to employees of Sematic.

We cut releases from the `main` branch, following these steps:

- Bump the version in `wheel_version.bzl`, `sematic/versions.py`,
  `helm/sematic-server/values.yaml`, and `helm/sematic-server/Chart.yaml`
- Update `changelog.md` with the new version number and any missing change
  entries
- Make the bump commit
- Build the UI:
```bash
$ make ui
```
- Build the wheel:
```bash
$ make wheel
```
- copy wheel from `bazel-bin/sematic/sematic-....whl` into a scratch directory,
and use a virtual env to test:

```bash
$ pip3 install <wheel path>
$ sematic start
$ sematic run examples/mnist/pytorch
```

Do this for all supported versions of Python. You can check your virtual env
Python version using `sematic version` (as well as the Server and Client
version).

If everything works fine, we are ready to push the release.

```bash
$ make test-release
$ make release
```

Once you have pushed it to PyPi, add the git tag.

```bash
$ export RELEASE_VERSION=v$(python3 ./sematic/versions.py)
$ git tag $RELEASE_VERSION
$ git push origin $RELEASE_VERSION
```

Next, build and push the server image. Use the dockerfile at
`docker/Dockerfile.server`. Copy the wheel you built before in the `docker/`
directory.
```bash
$ TAG=v$(python3 sematic/versions.py) make release-server
```

Finally, draft the release on GitHub. Add a "What's Changed" section, a
"New Contributors" section, a "Full Changelog" link, and attach the wheel in
the assets section.

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
