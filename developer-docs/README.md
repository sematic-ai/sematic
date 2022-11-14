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
Active settings:

SEMATIC_API_ADDRESS: http://127.0.0.1:5001
SEMATIC_API_KEY: XXX
```

When developing, we often need to switch the Server where we submit pipelines,
sometimes bundled together with other settings as well. In order to avoid
constantly editing this file manually, we can define one file per environment
or profile, under the names `~/.sematic/settings.yaml.<profile>`, and switch
between them using `bazel run //tools:switch-settings -- <profile>`.

This actually copies these profile files over the main settings file. Example:

```bash
$ bazel run //tools:switch-settings -- dev1
[...]
Copying previous settings to /Users/tudorscurtu/.sematic/settings.yaml_bck
Copying /Users/tudorscurtu/.sematic/settings.yaml.dev1 to /Users/tudorscurtu/.sematic/settings.yaml

Successfully switched to dev1!

$ sematic settings show
Active settings:

AWS_S3_BUCKET: XXX
KUBERNETES_NAMESPACE: XXX
SEMATIC_API_ADDRESS: https://XXX
SEMATIC_API_KEY: XXX
```

## Releasing
**Note:** Actually pushing the released wheel can only be done if you have
access to the PyPi repo, which is limited to employees of Sematic.

- Bump the version in `wheel_version.bzl`, `sematic/versions.py`,
  and `helm/sematic/values.yaml`
- Update `changelog.md` with the new version number
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
"Full Changelog" link, and attach the wheel in the assets section.
